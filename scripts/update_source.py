#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apps import APP_IDS, bundle_for, min_os_for  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="source.json")
    ap.add_argument("--app", required=True, choices=list(APP_IDS))
    ap.add_argument("--version", required=True)
    ap.add_argument("--build", required=True)
    ap.add_argument("--size", type=int, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--asset", required=True)
    ap.add_argument("--idempotent", action="store_true")
    ap.add_argument("--date", default=date.today().isoformat())
    args = ap.parse_args()

    with open(args.source) as handle:
        data = json.load(handle)
    bid = bundle_for(args.app)
    min_os = min_os_for(args.app)
    app = None
    for candidate in data["apps"]:
        if candidate["bundleIdentifier"] == bid:
            app = candidate
            break
    if app is None:
        print("app not found")
        sys.exit(1)

    expected_url = (
        f"https://github.com/jmargocubs/feather-apps/releases/download/"
        f"{args.tag}/{args.asset}"
    )
    for version in app.get("versions", []):
        if version.get("version") == args.version and version.get("buildVersion") == args.build:
            expected = {
                "version": args.version,
                "buildVersion": args.build,
                "downloadURL": expected_url,
                "size": args.size,
                "minOSVersion": min_os,
                "date": args.date,
            }
            if (
                args.idempotent
                and all(version.get(key) == value for key, value in expected.items())
                and app.get("size") == args.size
            ):
                print("source entry already matches", args.app, args.version, args.build)
                return
            if args.idempotent:
                print("existing source entry does not match expected release")
                sys.exit(1)
            print("duplicate version/build")
            sys.exit(1)

    entry = {
        "version": args.version,
        "buildVersion": args.build,
        "date": args.date,
        "downloadURL": expected_url,
        "size": args.size,
        "minOSVersion": min_os,
    }
    app.setdefault("versions", []).insert(0, entry)
    app["size"] = args.size
    with open(args.source, "w") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    print("updated", args.app, args.version, args.build)


if __name__ == "__main__":
    main()
