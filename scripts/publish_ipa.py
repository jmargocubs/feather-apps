#!/usr/bin/env python3
"""Publish a verified unsigned IPA to the shared AltStore-compatible source.

This is the single publishing engine for all four active apps. Local Mac
publishing and every GitHub Actions publish path (Kyro publish-approved-ipa,
Zepzi / Sunny Meadow build workflows, feather-apps Publish Beta) run this
script, so release tag, title, notes, IPA asset name, download URL and catalog
entry are identical in every environment (see apps.py "Shared release
metadata").

Approval gate: nothing is uploaded or pushed unless --approved is passed, and
--approved may only be passed for a build approved for distribution. Without
it the script validates the IPA, prints the exact publish plan (including the
catalog entry it would write) and exits 3 without publishing.

Catalog apps[].name is set to "App Name — Build N" for repository listings in
compatible signing apps. Installed IPA display names are never rewritten here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apps import (  # noqa: E402
    APP_IDS,
    APPS,
    SOURCE_REPO,
    asset_name_for,
    assert_version_policy,
    bundle_for,
    catalog_listing_name,
    download_url_for,
    min_os_for,
    release_notes_for,
    release_repo_for,
    release_target_for,
    release_title_for,
    tag_for,
)

NOT_APPROVED_EXIT = 3


SENSITIVE_NAME_FRAGMENTS = (
    ".p12",
    ".mobileprovision",
    ".p8",
    ".cer",
    "local.xcconfig",
    ".env",
    "id_rsa",
    "private_key",
    "provisioning",
)


def run(cmd: list[str], *, check: bool = True, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # gh may colorize JSON even when stdout is captured; force plain output.
    env["NO_COLOR"] = "1"
    env["CLICOLOR"] = "0"
    env.pop("CLICOLOR_FORCE", None)
    env["GH_FORCE_TTY"] = "0"
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if check and result.returncode:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"{result.stderr or result.stdout}"
        )
    return result


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def refuse_if_sensitive(path: pathlib.Path) -> None:
    lowered = path.name.lower()
    for fragment in SENSITIVE_NAME_FRAGMENTS:
        if fragment in lowered:
            raise RuntimeError(f"refusing to publish sensitive-looking file name: {path.name}")


def validate_and_scan(ipa: pathlib.Path, app: str, version: str, build: str) -> dict:
    # Per-app version policy (shared with every publish path); the IPA short
    # version must match the declared marketing version and CFBundleVersion the build.
    assert_version_policy(app, version, build)
    bundle = bundle_for(app)
    min_os = min_os_for(app)
    validate = run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_ipa.py"),
            str(ipa),
            "--bundle",
            bundle,
            "--version",
            version,
            "--build",
            str(build),
            "--minos",
            min_os,
        ]
    )
    print(validate.stdout, end="", file=sys.stderr)
    scan = run([sys.executable, str(ROOT / "scripts" / "scan_ipa.py"), str(ipa)])
    print(scan.stdout, end="", file=sys.stderr)
    size = ipa.stat().st_size
    digest = sha256_file(ipa)
    return {"bundle": bundle, "min_os": min_os, "size": size, "sha256": digest}


def release_exists(repo: str, tag: str) -> dict | None:
    result = run(
        ["gh", "api", f"repos/{repo}/releases/tags/{tag}"],
        check=False,
    )
    if result.returncode == 0:
        return json.loads(result.stdout)
    if "404" in (result.stderr or "") or "Not Found" in (result.stderr or ""):
        return None
    raise RuntimeError(f"failed to query release {tag}: {result.stderr or result.stdout}")


def create_or_resume_release(
    *,
    repo: str,
    tag: str,
    title: str,
    notes: str,
    ipa: pathlib.Path,
    asset_name: str,
    digest: str,
    size: int,
    target: str | None = None,
) -> dict:
    existing = release_exists(repo, tag)
    staged = ipa
    temp_dir = None
    try:
        if ipa.name != asset_name:
            temp_dir = pathlib.Path(tempfile.mkdtemp(prefix="source-publish-"))
            staged = temp_dir / asset_name
            shutil.copy2(ipa, staged)

        sha_sidecar = staged.with_suffix(staged.suffix + ".sha256")
        sha_sidecar.write_text(f"{digest}  {asset_name}\n", encoding="utf-8")

        if existing is None:
            run(
                [
                    "gh",
                    "release",
                    "create",
                    tag,
                    str(staged),
                    str(sha_sidecar),
                    "--repo",
                    repo,
                    "--title",
                    title,
                    "--notes",
                    notes,
                    "--prerelease",
                ]
                + (["--target", target] if target else [])
            )
            existing = release_exists(repo, tag)
            if existing is None:
                raise RuntimeError(f"release {tag} missing after create")
            print(f"created release {tag}")
        else:
            assets = existing.get("assets") or []
            ipa_assets = [a for a in assets if a.get("name") == asset_name]
            if not ipa_assets:
                run(
                    [
                        "gh",
                        "release",
                        "upload",
                        tag,
                        str(staged),
                        str(sha_sidecar),
                        "--repo",
                        repo,
                        "--clobber",
                    ]
                )
                existing = release_exists(repo, tag)
                print(f"uploaded missing assets to existing release {tag}")
            else:
                asset = ipa_assets[0]
                asset_size = int(asset.get("size") or 0)
                asset_digest = (asset.get("digest") or "").removeprefix("sha256:")
                if asset_size != size:
                    raise RuntimeError(
                        f"existing release asset size {asset_size} != expected {size}; refusing overwrite"
                    )
                if asset_digest and asset_digest != digest:
                    raise RuntimeError(
                        f"existing release asset digest {asset_digest} != expected {digest}; refusing overwrite"
                    )
                print(f"resuming exact existing release {tag}")
        return existing
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def update_catalog(
    *,
    app: str,
    version: str,
    build: str,
    size: int,
    tag: str,
    asset: str,
    download_url: str,
    release_date: str,
) -> None:
    common = [
        sys.executable,
        str(ROOT / "scripts" / "update_source.py"),
        "--idempotent",
        "--allow-create",
        "--app",
        app,
        "--version",
        version,
        "--build",
        str(build),
        "--size",
        str(size),
        "--tag",
        tag,
        "--asset",
        asset,
        "--download-url",
        download_url,
        "--date",
        release_date,
    ]
    result = run(common + ["--source", str(ROOT / "source.json")])
    print(result.stdout, end="")

    if APPS[app].get("update_tvos_source"):
        tvos_path = ROOT / "tvos-source.json"
        if not tvos_path.exists():
            tvos_path.write_text(
                json.dumps(
                    {
                        "name": "jmargocubs Apps — Apple TV",
                        "subtitle": "Kyro X tvOS beta builds",
                        "description": (
                            "AltStore-compatible tvOS source for Kyro X tvOS "
                            "beta IPAs hosted on GitHub Releases."
                        ),
                        "iconURL": APPS[app]["icon_url"],
                        "headerURL": None,
                        "website": "https://jmargocubs.github.io/feather-apps/",
                        "tintColor": APPS[app]["tint_color"],
                        "featuredApps": [],
                        "apps": [],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        result = run(common + ["--source", str(tvos_path)])
        print(result.stdout, end="")

    run([sys.executable, str(ROOT / "scripts" / "validate_source.py"), str(ROOT / "source.json")])
    if (ROOT / "tvos-source.json").exists():
        run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_source.py"),
                str(ROOT / "tvos-source.json"),
            ]
        )


def commit_and_push_source(app: str, version: str, build: str, dry_run: bool) -> str | None:
    status = run(["git", "status", "--porcelain", "--", "source.json", "tvos-source.json", "README.md", "docs/", "scripts/", "assets/"], cwd=ROOT)
    changed = [line for line in status.stdout.splitlines() if line.strip()]
    if not changed:
        print("catalog already committed")
        return None

    if dry_run:
        print("dry-run: skipping commit/push; local catalog updated")
        return None

    run(["git", "add", "source.json"], cwd=ROOT)
    if (ROOT / "tvos-source.json").exists():
        run(["git", "add", "tvos-source.json"], cwd=ROOT)
    # Include workflow/script/doc updates that belong with the permanent policy.
    for path in ("scripts/apps.py", "scripts/scan_ipa.py", "scripts/update_source.py", "scripts/publish_ipa.py", "README.md", "docs/release-process.md", "docs/nullsign-auto-publish.md"):
        if (ROOT / path).exists():
            run(["git", "add", path], cwd=ROOT, check=False)

    message = f"Publish {app} {version} build {build} to shared source catalog"
    run(["git", "commit", "-m", message], cwd=ROOT)
    # Several environments can write the catalog; rebase onto main and retry on a
    # non-fast-forward push. A rebase conflict aborts instead of overwriting.
    for attempt in range(1, 6):
        pushed = run(["git", "push", "origin", "HEAD:main"], cwd=ROOT, check=False)
        if pushed.returncode == 0:
            break
        if attempt == 5:
            raise RuntimeError(f"catalog push failed after retries: {pushed.stderr or pushed.stdout}")
        print(f"catalog push attempt {attempt} rejected; rebasing onto origin/main")
        run(["git", "fetch", "origin", "main"], cwd=ROOT)
        rebased = run(["git", "rebase", "origin/main"], cwd=ROOT, check=False)
        if rebased.returncode != 0:
            run(["git", "rebase", "--abort"], cwd=ROOT, check=False)
            raise RuntimeError("catalog rebase conflict; refusing to overwrite another publish")
        for path in ("source.json", "tvos-source.json"):
            if (ROOT / path).exists():
                run([sys.executable, str(ROOT / "scripts" / "validate_source.py"), str(ROOT / path)])
    sha = run(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.strip()
    print(f"pushed catalog update {sha}")
    return sha


def verify_public_asset(url: str, digest: str, size: int) -> None:
    run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_asset.py"),
            url,
            "--sha256",
            digest,
            "--size",
            str(size),
            "--attempts",
            "18",
            "--interval",
            "5",
        ]
    )


def rewrite_source_header() -> None:
    """Keep top-level source descriptions current without rewriting app history."""
    source_path = ROOT / "source.json"
    data = json.loads(source_path.read_text())
    data["subtitle"] = "Kyro X (iPhone and Apple TV), Zepzi and Sunny Meadow beta builds"
    data["description"] = (
        "App source for Kyro X, Kyro X tvOS, Zepzi and Sunny Meadow. "
        "Beta IPAs are unsigned and hosted on GitHub Releases; use any signing "
        "or sideloading app that reads the standard source.json format. "
        "Listings show App Name — Build N; the installed app name comes from "
        "each IPA and is not changed by this catalog."
    )
    source_path.write_text(json.dumps(data, indent=2) + "\n")


def build_plan(
    ipa: pathlib.Path,
    app: str,
    version: str,
    build: str,
    *,
    notes: str | None = None,
    source_commit: str | None = None,
) -> dict:
    """Validate the IPA and compute everything a publish would write.

    Shared by --approved runs and plan-only runs, so the printed plan is exactly
    what gets published.
    """
    meta = validate_and_scan(ipa, app, version, build)
    asset_name = asset_name_for(app, version, build)
    refuse_if_sensitive(pathlib.Path(asset_name))
    return {
        "app": app,
        "platform": APPS[app]["platform"],
        "bundle": meta["bundle"],
        "version": version,
        "build": build,
        "min_os": meta["min_os"],
        "release_repo": release_repo_for(app),
        "tag": tag_for(app, version, build),
        "target": release_target_for(app, source_commit),
        "title": release_title_for(app, version, build),
        "notes": release_notes_for(
            app, version, build, size=meta["size"], sha256=meta["sha256"],
            source_commit=source_commit, extra_notes=notes,
        ),
        "asset": asset_name,
        "download_url": download_url_for(app, version, build, asset_name),
        "size": meta["size"],
        "sha256": meta["sha256"],
        "listing_name": catalog_listing_name(app, build),
        "source_repo": SOURCE_REPO,
        "catalogs": ["source.json"] + (["tvos-source.json"] if APPS[app].get("update_tvos_source") else []),
    }


def preview_catalog_entries(plan: dict, release_date: str) -> dict:
    """Run update_source.py against temporary copies; return the resulting entries."""
    out = {}
    with tempfile.TemporaryDirectory(prefix="catalog-preview-") as tmp:
        for name in plan["catalogs"]:
            src = ROOT / name
            dst = pathlib.Path(tmp) / name
            shutil.copy2(src, dst)
            result = run(
                [
                    sys.executable, str(ROOT / "scripts" / "update_source.py"),
                    "--idempotent", "--allow-create", "--source", str(dst),
                    "--app", plan["app"], "--version", plan["version"], "--build", plan["build"],
                    "--size", str(plan["size"]), "--tag", plan["tag"], "--asset", plan["asset"],
                    "--download-url", plan["download_url"], "--date", release_date,
                ],
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"catalog preview failed for {name}: {result.stderr or result.stdout}")
            data = json.loads(dst.read_text())
            entry = next(a for a in data["apps"] if a["bundleIdentifier"] == plan["bundle"])
            out[name] = {
                "name": entry["name"],
                "bundleIdentifier": entry["bundleIdentifier"],
                "size": entry["size"],
                "head": entry["versions"][0],
            }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=pathlib.Path)
    parser.add_argument("--app", required=True, choices=list(APP_IDS))
    parser.add_argument("--version", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--notes", help="optional extra release notes (appended to the standard notes)")
    parser.add_argument("--source-commit", help="source commit SHA the IPA was built from")
    parser.add_argument(
        "--approved",
        action="store_true",
        help="the build is approved for distribution: upload the release and update the catalog",
    )
    parser.add_argument("--asset-name", help=argparse.SUPPRESS)  # deprecated; name is canonical
    parser.add_argument("--dry-run", action="store_true", help="plan only (same as omitting --approved)")
    parser.add_argument("--release-date", help="date used in the plan-only catalog preview")
    parser.add_argument("--skip-git", action="store_true", help="update local catalog only")
    args = parser.parse_args()

    ipa = args.ipa.expanduser().resolve()
    if not ipa.is_file():
        print(f"IPA not found: {ipa}", file=sys.stderr)
        return 1
    refuse_if_sensitive(ipa)

    app = args.app
    version = args.version
    build = str(args.build)
    plan = build_plan(ipa, app, version, build, notes=args.notes, source_commit=args.source_commit)
    if args.asset_name and args.asset_name != plan["asset"]:
        print(
            f"note: --asset-name {args.asset_name!r} ignored; canonical asset name is {plan['asset']!r}",
            file=sys.stderr,
        )

    if args.dry_run or not args.approved:
        plan["catalog_preview"] = preview_catalog_entries(plan, args.release_date or date.today().isoformat())
        print(json.dumps(plan, indent=2))
        if args.dry_run:
            print("dry-run: validation passed; nothing uploaded or pushed")
            return 0
        print(
            "NOT PUBLISHED: --approved was not given. Re-run with --approved only for a build "
            "approved for distribution.",
            file=sys.stderr,
        )
        return NOT_APPROVED_EXIT

    print(json.dumps(plan, indent=2))
    release = create_or_resume_release(
        repo=plan["release_repo"],
        tag=plan["tag"],
        title=plan["title"],
        notes=plan["notes"],
        ipa=ipa,
        asset_name=plan["asset"],
        digest=plan["sha256"],
        size=plan["size"],
        target=plan["target"],
    )
    release_date = (release.get("published_at") or release.get("created_at") or date.today().isoformat())[:10]

    verify_public_asset(plan["download_url"], plan["sha256"], plan["size"])

    rewrite_source_header()
    update_catalog(
        app=app,
        version=version,
        build=build,
        size=plan["size"],
        tag=plan["tag"],
        asset=plan["asset"],
        download_url=plan["download_url"],
        release_date=release_date,
    )

    if not args.skip_git:
        commit_and_push_source(app, version, build, dry_run=False)

    print("PUBLISH OK")
    print(f"release: https://github.com/{plan['release_repo']}/releases/tag/{plan['tag']}")
    print(f"ipa: {plan['download_url']}")
    print("source: https://jmargocubs.github.io/feather-apps/source.json")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001 - top-level CLI boundary
        print(f"PUBLISH FAILED: {error}", file=sys.stderr)
        print("Built IPA was left in place for retry.", file=sys.stderr)
        raise SystemExit(1)
