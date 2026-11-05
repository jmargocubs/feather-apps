#!/usr/bin/env python3
"""Stage a local IPA through an authenticated draft asset into an Actions artifact."""

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import uuid


ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLES = {"kyro": "com.cubbiestream.kyro", "zepzi": "app.flippy.reader"}


def run(*args, input_bytes=None, capture=True, check=True):
    result = subprocess.run(
        args,
        input=input_bytes,
        capture_output=capture,
        check=False,
        text=input_bytes is None,
    )
    if check and result.returncode:
        stderr = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(args)}\n{stderr}")
    return result


def gh_json(*args):
    result = run("gh", *args)
    return json.loads(result.stdout)


def checksum(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def delete_draft(repo, release_id):
    if not release_id:
        return
    run(
        "gh",
        "api",
        "--method",
        "DELETE",
        f"repos/{repo}/releases/{release_id}",
        capture=True,
        check=False,
    )


def find_new_run(repo, ref, artifact_name, previous_ids):
    deadline = time.time() + 90
    while time.time() < deadline:
        runs = gh_json(
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            "publish-beta.yml",
            "--branch",
            ref,
            "--event",
            "workflow_dispatch",
            "--limit",
            "30",
            "--json",
            "databaseId,displayTitle,status,url",
        )
        for item in runs:
            if item["databaseId"] not in previous_ids and artifact_name in item["displayTitle"]:
                return item
        time.sleep(2)
    raise RuntimeError("timed out waiting for the staging workflow run to appear")


def main():
    parser = argparse.ArgumentParser(
        description="Upload a local IPA to a temporary authenticated draft release, then dispatch "
        "Publish Beta in stage mode to create a seven-day Actions artifact."
    )
    parser.add_argument("ipa", type=pathlib.Path)
    parser.add_argument("--app", required=True, choices=sorted(BUNDLES))
    parser.add_argument("--version", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--repo", default="jmargocubs/feather-apps")
    parser.add_argument("--ref", default="main")
    parser.add_argument("--artifact-name")
    args = parser.parse_args()

    ipa = args.ipa.expanduser().resolve()
    if not ipa.is_file():
        parser.error(f"IPA not found: {ipa}")
    artifact_name = args.artifact_name or f"{args.app}-ipa-candidate"
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", artifact_name):
        parser.error("artifact name must start with a lowercase letter or digit and use only . _ or -")

    run(
        sys.executable,
        str(ROOT / "scripts" / "validate_ipa.py"),
        str(ipa),
        "--bundle",
        BUNDLES[args.app],
        "--version",
        args.version,
        "--build",
        args.build,
        "--minos",
        "18.0",
        capture=False,
    )
    run(sys.executable, str(ROOT / "scripts" / "scan_ipa.py"), str(ipa), capture=False)
    sha256 = checksum(ipa)
    size = ipa.stat().st_size

    run("gh", "auth", "status", "--hostname", "github.com", capture=True)
    prior = gh_json(
        "run",
        "list",
        "--repo",
        args.repo,
        "--workflow",
        "publish-beta.yml",
        "--branch",
        args.ref,
        "--event",
        "workflow_dispatch",
        "--limit",
        "30",
        "--json",
        "databaseId",
    )
    previous_ids = {item["databaseId"] for item in prior}

    request_id = uuid.uuid4().hex[:12]
    tag = f"staging-{args.app}-{request_id}"
    run(
        "gh",
        "release",
        "create",
        tag,
        str(ipa),
        "--repo",
        args.repo,
        "--draft",
        "--target",
        "main",
        "--title",
        f"Temporary IPA staging {request_id}",
        "--notes",
        "Temporary authenticated transport for Publish Beta staging; never publish.",
    )
    releases = gh_json("api", f"repos/{args.repo}/releases?per_page=100")
    matches = [item for item in releases if item["tag_name"] == tag and item["draft"]]
    if len(matches) != 1:
        raise RuntimeError(f"expected one draft release for {tag}, found {len(matches)}")
    release = matches[0]
    release_id = release["id"]
    try:
        assets = [item for item in release["assets"] if item["name"] == ipa.name]
        if len(assets) != 1:
            raise RuntimeError(f"expected one uploaded asset named {ipa.name}, found {len(assets)}")
        asset = assets[0]

        run(
            "gh",
            "workflow",
            "run",
            "publish-beta.yml",
            "--repo",
            args.repo,
            "--ref",
            args.ref,
            "-f",
            "operation=stage",
            "-f",
            f"app={args.app}",
            "-f",
            f"artifact_name={artifact_name}",
            "-f",
            f"expected_sha256={sha256}",
            "-f",
            f"expected_size={size}",
            "-f",
            f"staging_locator={release_id}:{asset['id']}",
        )
        workflow_run = find_new_run(args.repo, args.ref, artifact_name, previous_ids)
        run(
            "gh",
            "run",
            "watch",
            str(workflow_run["databaseId"]),
            "--repo",
            args.repo,
            "--exit-status",
            capture=False,
        )
        artifacts = gh_json(
            "api", f"repos/{args.repo}/actions/runs/{workflow_run['databaseId']}/artifacts"
        )["artifacts"]
        matches = [item for item in artifacts if item["name"] == artifact_name and not item["expired"]]
        if len(matches) != 1:
            raise RuntimeError(f"expected one non-expired {artifact_name!r} artifact, found {len(matches)}")
        result = {
            "artifact_name": artifact_name,
            "artifact_id": matches[0]["id"],
            "artifact_run_id": workflow_run["databaseId"],
            "artifact_digest": matches[0].get("digest"),
            "ipa_sha256": sha256,
            "ipa_size": size,
            "workflow_url": workflow_run["url"],
        }
        print(json.dumps(result, indent=2))
        release_id = None  # The successful workflow deleted it.
    finally:
        delete_draft(args.repo, release_id)


if __name__ == "__main__":
    main()
