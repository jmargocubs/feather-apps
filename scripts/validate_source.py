#!/usr/bin/env python3
"""Validate an AltStore-compatible source file.

Besides structure, this enforces the catalog policy from the 2026-11-27 audit:
only the active listings in scripts/apps.py APPS may appear, and retired
listings (RETIRED_APPS) are refused so old workflows or stale checkouts cannot
re-add them.
"""
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from apps import assert_catalog_allowed  # noqa: E402


def main(path):
    with open(path) as f:
        data = json.load(f)
    assert "apps" in data and isinstance(data["apps"], list)
    ids = set()
    for app in data["apps"]:
        bid = app["bundleIdentifier"]
        assert bid not in ids, f"duplicate bundle id {bid}"
        ids.add(bid)
        for v in app.get("versions", []):
            assert "version" in v and "buildVersion" in v
            assert str(v.get("downloadURL","")).startswith("https://")
            assert v.get("size",0) > 0
    is_tvos = os.path.basename(path).startswith("tvos-")
    try:
        assert_catalog_allowed(data, tvos=is_tvos)
    except ValueError as exc:
        raise SystemExit(f"catalog policy violation in {path}: {exc}")
    print("source valid:", len(data["apps"]), "apps")
    print("OK")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv)>1 else "source.json")
