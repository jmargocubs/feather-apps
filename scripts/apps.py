#!/usr/bin/env python3
"""Canonical app catalog for Feather beta publishing."""

from __future__ import annotations

import json
import sys

APPS = {
    "kyro": {
        "bundle": "com.cubbiestream.kyro",
        "min_os": "18.0",
        "display_name": "Kyro",
    },
    "zepzi": {
        "bundle": "app.flippy.reader",
        "min_os": "18.0",
        "display_name": "Zepzi",
    },
    "sunnymeadow": {
        "bundle": "com.sunnymeadow.app.beta",
        "min_os": "17.0",
        "display_name": "Sunny Meadow",
    },
}

APP_IDS = tuple(sorted(APPS))
APP_CHOICE_RE = "^(?:%s)$" % "|".join(APP_IDS)


def bundle_for(app: str) -> str:
    return APPS[app]["bundle"]


def min_os_for(app: str) -> str:
    return APPS[app]["min_os"]


def main(argv: list[str]) -> int:
    if len(argv) == 1 or argv[1] in {"-h", "--help"}:
        print(
            "usage: apps.py ids|choice-re|json|bundle <app>|minos <app>",
            file=sys.stderr,
        )
        return 2
    cmd = argv[1]
    if cmd == "ids":
        print(" ".join(APP_IDS))
        return 0
    if cmd == "choice-re":
        print(APP_CHOICE_RE)
        return 0
    if cmd == "json":
        print(json.dumps(APPS, indent=2, sort_keys=True))
        return 0
    if cmd in {"bundle", "minos"} and len(argv) == 3:
        app = argv[2]
        if app not in APPS:
            print(f"unknown app: {app}", file=sys.stderr)
            return 1
        print(bundle_for(app) if cmd == "bundle" else min_os_for(app))
        return 0
    print("usage: apps.py ids|choice-re|json|bundle <app>|minos <app>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
