#!/usr/bin/env python3
"""Insert or resume an exact app version entry in an AltStore-compatible source.json."""

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
    assert_version_aligned_with_build,
    base_name_for,
    bundle_for,
    catalog_listing_name,
    current_listing_name,
    min_os_for,
)


def find_app(data: dict, bundle_id: str):
    for candidate in data.get("apps", []):
        if candidate.get("bundleIdentifier") == bundle_id:
            return candidate
    return None


def apply_catalog_metadata(app: dict, app_id: str, versions: list[dict], build: str) -> None:
    """Refresh listing/display metadata without rewriting version history rows."""
    meta = APPS[app_id]
    app["name"] = current_listing_name(app_id, versions, build)
    app["subtitle"] = meta["subtitle"]
    app["localizedDescription"] = meta["localized_description"]
    app["iconURL"] = meta["icon_url"]
    app["tintColor"] = meta["tint_color"]


def ensure_app(data: dict, app_id: str, build: str) -> dict:
    meta = APPS[app_id]
    bundle_id = meta["bundle"]
    existing = find_app(data, bundle_id)
    if existing is not None:
        return existing
    entry = {
        "name": catalog_listing_name(app_id, build),
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


def newest_build(
    versions: list[dict], marketing_version: str | None = None
) -> int | None:
    """Highest buildVersion across rows.

    When ``marketing_version`` is set, only that marketing string is considered
    (legacy). New publishes use unique major.minor.<build> strings, so callers
    should pass ``marketing_version=None`` to compare build numbers globally and
    refuse duplicates/downgrades across old 1.0.0 rows and new 1.0.N rows.
    """
    builds = []
    for version in versions:
        if marketing_version is not None and version.get("version") != marketing_version:
            continue
        try:
            builds.append(int(str(version.get("buildVersion"))))
        except (TypeError, ValueError):
            continue
    return max(builds) if builds else None


def refresh_listing_names(data: dict) -> int:
    """Set each known app's listing title from its current head build. Returns changes."""
    changed = 0
    by_bundle = {meta["bundle"]: app_id for app_id, meta in APPS.items()}
    for app in data.get("apps", []):
        app_id = by_bundle.get(app.get("bundleIdentifier"))
        if app_id is None:
            continue
        versions = app.get("versions") or []
        if not versions:
            continue
        desired = current_listing_name(app_id, versions, versions[0].get("buildVersion"))
        if app.get("name") != desired:
            app["name"] = desired
            changed += 1
        # Keep stem documentation stable; never invent IPA display names here.
        if base_name_for(app_id) not in str(app.get("name") or ""):
            raise RuntimeError(f"listing name missing base title for {app_id}")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="source.json")
    parser.add_argument("--app", choices=list(APP_IDS))
    parser.add_argument("--version")
    parser.add_argument("--build")
    parser.add_argument("--size", type=int)
    parser.add_argument("--tag")
    parser.add_argument("--asset")
    parser.add_argument("--download-url")
    parser.add_argument("--idempotent", action="store_true")
    parser.add_argument("--allow-create", action="store_true")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument(
        "--refresh-listing-names",
        action="store_true",
        help="rewrite apps[].name from each head build without adding versions",
    )
    args = parser.parse_args()

    source_path = pathlib.Path(args.source)
    with source_path.open() as handle:
        data = json.load(handle)

    if args.refresh_listing_names:
        changed = refresh_listing_names(data)
        with source_path.open("w") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        print(f"refreshed listing names: {changed} app(s) updated")
        return

    required = [args.app, args.version, args.build, args.size, args.tag, args.asset]
    if any(value is None for value in required):
        print(
            "app, version, build, size, tag, and asset are required unless "
            "--refresh-listing-names is set",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.allow_create:
        app = ensure_app(data, args.app, str(args.build))
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
            if args.idempotent and comparable == expected and app.get("size") == args.size:
                desired_name = current_listing_name(
                    args.app, app.get("versions", []), args.build
                )
                if app.get("name") == desired_name:
                    print("source entry already matches", args.app, args.version, args.build)
                    return
                # Exact release row already present; only refresh listing title.
                apply_catalog_metadata(app, args.app, app.get("versions", []), str(args.build))
                with source_path.open("w") as handle:
                    json.dump(data, handle, indent=2)
                    handle.write("\n")
                print(
                    "source entry already matches; refreshed listing name",
                    args.app,
                    desired_name,
                )
                return
            if args.idempotent:
                print("existing source entry does not match expected release", file=sys.stderr)
                sys.exit(1)
            print("duplicate version/build", file=sys.stderr)
            sys.exit(1)

    # New catalog rows must use major.minor.<build>. Legacy rows may still be
    # resumed above without rewriting history.
    try:
        assert_version_aligned_with_build(str(args.version), str(args.build))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    try:
        build_number = int(str(args.build))
    except ValueError:
        print("build must be an integer", file=sys.stderr)
        sys.exit(1)

    # Compare build numbers across all marketing versions so a new 1.0.104 row
    # cannot land after 1.0.0/105 or 1.0.105/105.
    current_newest = newest_build(app.get("versions", []), marketing_version=None)
    if current_newest is not None and build_number < current_newest:
        print(
            f"refusing to publish older build {build_number} when {current_newest} exists",
            file=sys.stderr,
        )
        sys.exit(1)
    if current_newest is not None and build_number == current_newest:
        # Exact version+build resume is handled above; reaching here means the
        # same build exists under a different marketing version string.
        print(
            f"refusing duplicate buildVersion {build_number} under a different version string",
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
    # Keep catalog listing title current without rewriting unrelated apps or history.
    apply_catalog_metadata(app, args.app, app.get("versions", []), str(args.build))

    with source_path.open("w") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    print("updated", args.app, args.version, args.build, "listing", app["name"])


if __name__ == "__main__":
    main()
