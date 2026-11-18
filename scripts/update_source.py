#!/usr/bin/env python3
"""Insert or resume an exact app version entry in a Nullsign-compatible source.json."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apps import (  # noqa: E402
    APP_IDS,
    APPS,
    bundle_for,
    min_os_for,
)


def find_app(data: dict, bundle_id: str):
    for candidate in data.get("apps", []):
        if candidate.get("bundleIdentifier") == bundle_id:
            return candidate
    return None


def ensure_app(data: dict, app_id: str) -> dict:
    meta = APPS[app_id]
    bundle_id = meta["bundle"]
    existing = find_app(data, bundle_id)
    if existing is not None:
        return existing
    entry = {
        "name": meta["source_name"],
        "bundleIdentifier": bundle_id,
        "developerName": "jmargocubs",
        "subtitle": meta["subtitle"],
        "localizedDescription": meta["localized_description"],
        "iconURL": meta["icon_url"],
        "tintColor": meta["tint_color"],
        "size": 0,
        "versions": [],
    }
    data.setdefault("apps", []).append(entry)
    return entry


def newest_build(versions: list[dict], marketing_version: str) -> int | None:
    builds = []
    for version in versions:
        if version.get("version") != marketing_version:
            continue
        try:
            builds.append(int(str(version.get("buildVersion"))))
        except (TypeError, ValueError):
            continue
    return max(builds) if builds else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="source.json")
    parser.add_argument("--app", required=True, choices=list(APP_IDS))
    parser.add_argument("--version", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--download-url")
    parser.add_argument("--idempotent", action="store_true")
    parser.add_argument("--allow-create", action="store_true")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    source_path = pathlib.Path(args.source)
    with source_path.open() as handle:
        data = json.load(handle)

    if args.allow_create:
        app = ensure_app(data, args.app)
    else:
        app = find_app(data, bundle_for(args.app))
        if app is None:
            print("app not found", file=sys.stderr)
            sys.exit(1)

    expected_url = args.download_url or (
        f"https://github.com/{APPS[args.app]['release_repo']}/releases/download/"
        f"{args.tag}/{args.asset}"
    )

    min_os = min_os_for(args.app)
    expected = {
        "version": args.version,
        "buildVersion": str(args.build),
        "downloadURL": expected_url,
        "size": args.size,
        "minOSVersion": min_os,
        "date": args.date,
    }

    for version in app.get("versions", []):
        if (
            version.get("version") == args.version
            and str(version.get("buildVersion")) == str(args.build)
        ):
            comparable = {
                "version": version.get("version"),
                "buildVersion": str(version.get("buildVersion")),
                "downloadURL": version.get("downloadURL"),
                "size": version.get("size"),
                "minOSVersion": version.get("minOSVersion"),
                "date": version.get("date"),
            }
            if (
                args.idempotent
                and comparable == expected
                and app.get("size") == args.size
            ):
                print("source entry already matches", args.app, args.version, args.build)
                return
            if args.idempotent:
                print("existing source entry does not match expected release", file=sys.stderr)
                sys.exit(1)
            print("duplicate version/build", file=sys.stderr)
            sys.exit(1)

    try:
        build_number = int(str(args.build))
    except ValueError:
        print("build must be an integer", file=sys.stderr)
        sys.exit(1)

    current_newest = newest_build(app.get("versions", []), args.version)
    if current_newest is not None and build_number < current_newest:
        print(
            f"refusing to publish older build {build_number} when {current_newest} exists",
            file=sys.stderr,
        )
        sys.exit(1)

    entry = {
        "version": args.version,
        "buildVersion": str(args.build),
        "date": args.date,
        "downloadURL": expected_url,
        "size": args.size,
        "minOSVersion": min_os,
    }
    app.setdefault("versions", []).insert(0, entry)
    app["size"] = args.size
    # Keep catalog display fields current without rewriting unrelated apps.
    meta = APPS[args.app]
    app["name"] = meta["source_name"]
    app["subtitle"] = meta["subtitle"]
    app["localizedDescription"] = meta["localized_description"]
    app["iconURL"] = meta["icon_url"]
    app["tintColor"] = meta["tint_color"]

    with source_path.open("w") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    print("updated", args.app, args.version, args.build)


if __name__ == "__main__":
    main()
