#!/usr/bin/env python3
"""Canonical app catalog for AltStore-compatible beta publishing."""

from __future__ import annotations

import json
import re
import sys

# Hosting:
# - Kyro iOS / tvOS IPAs live on jmargocubs/Kyro releases.
# - Zepzi / Sunny Meadow IPAs live on jmargocubs/feather-apps releases.
# Catalog metadata always lives in jmargocubs/feather-apps source.json
# (AltStore-compatible source used by signing / sideloading apps).
#
# Listing title vs installed name:
# - source.json apps[].name is the repository listing title shown by compatible
#   signing apps. It is generated as "{source_name} — Build {N}".
# - The name inside the installed IPA (CFBundleDisplayName / bundle display name)
#   is never rewritten by this catalog.
LISTING_NAME_SEP = " — Build "
_LISTING_NAME_RE = re.compile(r"^(?P<base>.+?) — Build (?P<build>\S+)$")

APPS = {
    "kyro": {
        "bundle": "com.cubbiestream.kyro",
        "min_os": "18.0",
        "display_name": "Kyro",
        "platform": "ios",
        "release_repo": "jmargocubs/Kyro",
        "tag_template": "kyro-ios-v{version}-build{build}-rc1",
        "source_name": "Kyro",
        "subtitle": "Self-hosted media streaming client",
        "localized_description": (
            "Kyro is a customized iOS streaming client based on Silo, bringing "
            "your self-hosted media library together with an enhanced IPTV "
            "experience and Sports Hub features. Enjoy movies, TV shows, live "
            "channels, a personalized interface, and more in one app. Built for "
            "users who want greater control over their streaming experience. "
            "Sports Hub features are in development."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/kyro/icon.png",
        "tint_color": "#4F46E5",
        "update_tvos_source": False,
    },
    "kyro-tvos": {
        "bundle": "com.cubbiestream.kyro.tvos",
        "min_os": "26.0",
        "display_name": "Kyro Apple TV",
        "platform": "tvos",
        "release_repo": "jmargocubs/Kyro",
        "tag_template": "kyro-tvos-v{version}-build{build}-rc1",
        "source_name": "Kyro Apple TV",
        "subtitle": "Self-hosted media streaming client for Apple TV",
        "localized_description": (
            "Kyro Apple TV is a tvOS streaming client for self-hosted media "
            "libraries, live channels, and Sports Hub features. This unsigned "
            "beta requires your own signing and sideloading setup."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/kyro/icon.png",
        "tint_color": "#4F46E5",
        "update_tvos_source": True,
    },
    "zepzi": {
        "bundle": "app.flippy.reader",
        "min_os": "18.0",
        "display_name": "Zepzi",
        "platform": "ios",
        "release_repo": "jmargocubs/feather-apps",
        "tag_template": "zepzi-v{version}-b{build}",
        "source_name": "Zepzi",
        "subtitle": "Comic reader for Komga",
        "localized_description": (
            "Zepzi is a colorful, customizable comic-reading app for iPhone, "
            "built for readers who host their collections with Komga. Explore "
            "your library, enjoy a smooth reading experience, track your "
            "progress, unlock achievements, and personalize your adventure "
            "with unique themes."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/zepzi/icon.png",
        "tint_color": "#4F46E5",
        "update_tvos_source": False,
    },
    "sunnymeadow": {
        "bundle": "com.sunnymeadow.app.beta",
        "min_os": "17.0",
        "display_name": "Sunny Meadow",
        "platform": "ios",
        "release_repo": "jmargocubs/feather-apps",
        "tag_template": "sunnymeadow-v{version}-b{build}",
        "source_name": "Sunny Meadow",
        "subtitle": "Private recovery and mood journaling",
        "localized_description": (
            "Sunny Meadow is a calm, private iPhone app for mood check-ins and "
            "Recovery Journeys. Track how you feel, keep gentle recovery "
            "journeys with your own intention, and watch a Living Tree grow as "
            "you show up. Personal data stays on your device. This beta build "
            "is unsigned; testers must use their own signing setup."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/sunnymeadow/icon.png",
        "tint_color": "#EA580C",
        "update_tvos_source": False,
    },
}

APP_IDS = tuple(sorted(APPS))
APP_CHOICE_RE = "^(?:%s)$" % "|".join(APP_IDS)
SOURCE_REPO = "jmargocubs/feather-apps"
SOURCE_URL = "https://jmargocubs.github.io/feather-apps/source.json"
TVOS_SOURCE_URL = "https://jmargocubs.github.io/feather-apps/tvos-source.json"


def bundle_for(app: str) -> str:
    return APPS[app]["bundle"]


def min_os_for(app: str) -> str:
    return APPS[app]["min_os"]


def release_repo_for(app: str) -> str:
    return APPS[app]["release_repo"]


def base_name_for(app: str) -> str:
    """Stable product name used inside docs and as the listing-name stem.

    This is not written into IPA Info.plist; installed app titles stay whatever
    the binary already ships.
    """
    return APPS[app]["source_name"]


def catalog_listing_name(app: str, build: str | int) -> str:
    """Repository listing title: 'App Name — Build N'."""
    return f"{base_name_for(app)}{LISTING_NAME_SEP}{build}"


def parse_catalog_listing_name(name: str) -> tuple[str, str] | None:
    match = _LISTING_NAME_RE.match(str(name or ""))
    if not match:
        return None
    return match.group("base"), match.group("build")


def current_listing_name(app: str, versions: list[dict], fallback_build: str | int) -> str:
    """Listing title for the current head row (versions[0]) or fallback build."""
    if versions:
        head_build = versions[0].get("buildVersion", fallback_build)
        return catalog_listing_name(app, head_build)
    return catalog_listing_name(app, fallback_build)


def tag_for(app: str, version: str, build: str) -> str:
    return APPS[app]["tag_template"].format(version=version, build=build)


def download_url_for(app: str, version: str, build: str, asset: str) -> str:
    tag = tag_for(app, version, build)
    repo = release_repo_for(app)
    return f"https://github.com/{repo}/releases/download/{tag}/{asset}"


def visible_marketing_version(base: str, build: str | int) -> str:
    """Compose the signing-app visible marketing version: major.minor.<build>.

    ``base`` is the product's major.minor (or major.minor.patch) stem, for
    example ``1.0.0``, ``1.0``, or ``0.3.0``. The build number becomes the
    patch component so Feather / AltStore-style clients show ``1.0.105``
    instead of ``1.0.0 (105)``.

    Idempotent when ``base`` is already ``major.minor.<build>``. Always keeps
    the existing major and minor; never appends an extra ``.<build>`` suffix
    onto an already-aligned version.
    """
    build_s = str(build).strip()
    if not build_s.isdigit():
        raise ValueError(f"build must be numeric digits, got {build!r}")
    parts = str(base).strip().split(".")
    if len(parts) < 2:
        raise ValueError(f"base version must be major.minor[.patch], got {base!r}")
    major, minor = parts[0], parts[1]
    if not major.isdigit() or not minor.isdigit():
        raise ValueError(f"base version must be numeric major.minor, got {base!r}")
    return f"{major}.{minor}.{build_s}"


def assert_version_aligned_with_build(version: str, build: str | int) -> str:
    """Require catalog/IPA CFBundleShortVersionString == major.minor.<build>."""
    expected = visible_marketing_version(version, build)
    if str(version).strip() != expected:
        raise ValueError(
            f"version {version!r} must equal visible marketing version {expected!r} "
            f"for build {build}"
        )
    return expected


def main(argv: list[str]) -> int:
    if len(argv) == 1 or argv[1] in {"-h", "--help"}:
        print(
            "usage: apps.py ids|choice-re|json|bundle <app>|minos <app>|repo <app>|"
            "listing-name <app> <build>|tag <app> <version> <build>|"
            "visible-version <base> <build>",
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
    if cmd in {"bundle", "minos", "repo"} and len(argv) == 3:
        app = argv[2]
        if app not in APPS:
            print(f"unknown app: {app}", file=sys.stderr)
            return 1
        if cmd == "bundle":
            print(bundle_for(app))
        elif cmd == "minos":
            print(min_os_for(app))
        else:
            print(release_repo_for(app))
        return 0
    if cmd == "listing-name" and len(argv) == 4:
        app, build = argv[2], argv[3]
        if app not in APPS:
            print(f"unknown app: {app}", file=sys.stderr)
            return 1
        print(catalog_listing_name(app, build))
        return 0
    if cmd == "tag" and len(argv) == 5:
        app, version, build = argv[2], argv[3], argv[4]
        if app not in APPS:
            print(f"unknown app: {app}", file=sys.stderr)
            return 1
        print(tag_for(app, version, build))
        return 0
    if cmd == "visible-version" and len(argv) == 4:
        try:
            print(visible_marketing_version(argv[2], argv[3]))
        except ValueError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0
    print(
        "usage: apps.py ids|choice-re|json|bundle <app>|minos <app>|repo <app>|"
        "listing-name <app> <build>|tag <app> <version> <build>|"
        "visible-version <base> <build>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
