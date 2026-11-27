#!/usr/bin/env python3
"""Canonical app catalog for AltStore-compatible beta publishing."""

from __future__ import annotations

import json
import re
import sys

# Hosting:
# - Kyro X iOS / tvOS IPAs live on jmargocubs/Kyro releases.
# - Zepzi / Sunny Meadow IPAs live on jmargocubs/feather-apps releases.
# Catalog metadata always lives in jmargocubs/feather-apps source.json
# (AltStore-compatible source for compatible source clients).
#
# Listing title vs installed name:
# - source.json apps[].name is the repository listing title shown by compatible
#   source clients. It is generated as "{source_name} — Build {N}".
# - The name inside the installed IPA (CFBundleDisplayName / bundle display name)
#   is never rewritten by this catalog.
# - Marketing version (CFBundleShortVersionString / versions[].version) and build
#   (CFBundleVersion / versions[].buildVersion) are independent fields.
LISTING_NAME_SEP = " — Build "
_LISTING_NAME_RE = re.compile(r"^(?P<base>.+?) — Build (?P<build>\S+)$")

APPS = {
    "kyro": {
        "bundle": "com.cubbiestream.kyro",
        "min_os": "18.0",
        "display_name": "Kyro X iOS",
        "platform": "ios",
        "release_repo": "jmargocubs/Kyro",
        "tag_template": "kyro-ios-v{version}-build{build}-rc1",
        "source_name": "Kyro X iOS",
        "subtitle": "Kyro X for iPhone: Silo media, Live TV, Sports, Radio and Podcasts",
        "localized_description": (
            "Kyro X is the iPhone streaming client built on Silo. It brings "
            "your self-hosted movies and shows together with Live TV and guide, "
            "a Sports Hub, internet Radio and Podcasts. Same app and bundle as "
            "earlier Kyro builds, so existing installs update in place. This "
            "unsigned beta requires your own signing and sideloading setup."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/kyro/icon.png",
        "tint_color": "#4F46E5",
        "update_tvos_source": False,
    },
    "kyro-tvos": {
        "bundle": "com.cubbiestream.kyro.tvos",
        "min_os": "26.0",
        "display_name": "Kyro X tvOS",
        "platform": "tvos",
        "release_repo": "jmargocubs/Kyro",
        "tag_template": "kyro-tvos-v{version}-build{build}-rc1",
        "source_name": "Kyro X tvOS",
        "subtitle": "Kyro X for Apple TV: Live TV, guide and Sports",
        "localized_description": (
            "Kyro X tvOS is the Apple TV streaming client for self-hosted media "
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

# Retired listings (audit 2026-11-27, approved by Jon). Removed from the catalog
# only: their source code, tags, GitHub releases and historical IPA assets are kept.
# They are deliberately NOT in APPS, so no script, CLI choice or workflow can publish
# them, and validate_source.py / update_source.py refuse any catalog that contains
# one of these bundle IDs. Re-activating one requires an explicit decision and a
# code change here.
RETIRED_APPS = {
    # Kyro Labs: experimental builds of Kyro on its own bundle ID, so it installs beside stable
    # Kyro and never replaces it. Its tags, listing, versions and builds are tracked separately
    # (source.json is keyed by bundle ID). Never reuse "kyro"'s bundle, tag template or listing.
    "kyro-labs": {
        "bundle": "com.cubbiestream.kyro.labs",
        "min_os": "18.0",
        "display_name": "Kyro X Labs",
        "platform": "ios",
        "release_repo": "jmargocubs/Kyro",
        "tag_template": "kyro-labs-ios-v{version}-build{build}-rc1",
        "source_name": "Kyro X Labs",
        "subtitle": "Experimental iPhone builds of Kyro (separate install)",
        "localized_description": (
            "Kyro X Labs is the experimental iPhone edition of Kyro, used to "
            "try features such as upstream Silo updates and additional media "
            "servers before they reach the main Kyro app. It installs "
            "separately from Kyro, keeps its own data and sign-in, and may be "
            "less stable. This unsigned beta requires your own signing and "
            "sideloading setup."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/kyro-x-labs/icon.png",
        "tint_color": "#F59E0B",
        "update_tvos_source": False,
    },
    # Kyro Labs Apple TV: experimental tvOS builds on their own bundle ID, beside Kyro Apple TV.
    # Never reuse "kyro-tvos"'s bundle, tag template or listing.
    "kyro-labs-tvos": {
        "bundle": "com.cubbiestream.kyro.tvos.labs",
        "min_os": "26.0",
        "display_name": "Kyro Labs",
        "platform": "tvos",
        "release_repo": "jmargocubs/Kyro",
        "tag_template": "kyro-labs-tvos-v{version}-build{build}-rc1",
        "source_name": "Kyro Labs Apple TV",
        "subtitle": "Experimental Apple TV builds of Kyro (separate install)",
        "localized_description": (
            "Kyro Labs Apple TV is the experimental edition of Kyro for tvOS. It "
            "installs separately from Kyro Apple TV, keeps its own data and "
            "sign-in, and may be less stable. This unsigned beta requires your "
            "own signing and sideloading setup."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/kyro-labs/icon.png",
        "tint_color": "#F59E0B",
        "update_tvos_source": True,
    },
    "kyrox": {
        "bundle": "com.cubbiestream.kyrox",
        "min_os": "18.0",
        "display_name": "Kyro X",
        "platform": "ios",
        "release_repo": "jmargocubs/feather-apps",
        "tag_template": "kyrox-v{version}-b{build}",
        "source_name": "Kyro X",
        "subtitle": "Separate independent Kyro X rebuild (Jellyfin, Silo, IPTV)",
        "localized_description": (
            "Kyro X (independent) is a separate, from-scratch iPhone streaming "
            "client with local profiles, direct Jellyfin and Silo server "
            "integration, IPTV support and a cinematic player. It is a "
            "different app from the main Kyro listing and installs beside it, "
            "even though both may show Kyro X on the Home Screen. This unsigned "
            "beta requires your own signing and sideloading setup."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/kyrox/icon.png",
        "tint_color": "#DC2626",
        "update_tvos_source": False,
    },
}
RETIRED_BUNDLES = frozenset(meta["bundle"] for meta in RETIRED_APPS.values())

# The catalog carries exactly these active listings (audit 2026-11-27).
ACTIVE_BUNDLES = frozenset(meta["bundle"] for meta in APPS.values())
TVOS_SOURCE_BUNDLES = frozenset(
    meta["bundle"] for meta in APPS.values() if meta.get("update_tvos_source")
)


def assert_catalog_allowed(data: dict, *, tvos: bool = False) -> None:
    """Refuse a catalog containing retired or unknown listings."""
    allowed = TVOS_SOURCE_BUNDLES if tvos else ACTIVE_BUNDLES
    for app in data.get("apps", []):
        bundle = app.get("bundleIdentifier")
        if bundle in RETIRED_BUNDLES:
            raise ValueError(f"retired listing {bundle} must not be in the catalog")
        if bundle not in allowed:
            raise ValueError(f"unknown listing {bundle} is not an active catalog app")

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


_MARKETING_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)*$")
_BUILD_VERSION_RE = re.compile(r"^\d+$")


def assert_independent_version_fields(version: str, build: str | int) -> tuple[str, str]:
    """Validate marketing version and build as independent fields.

    Catalog ``version`` / IPA ``CFBundleShortVersionString`` may be any numeric
    dotted marketing string (for example ``1.0.0`` or ``0.3.0``). Catalog
    ``buildVersion`` / IPA ``CFBundleVersion`` must be decimal digits. The
    marketing patch component is never required to equal the build number.
    Listing titles carry the build via ``App Name — Build N``.
    """
    version_s = str(version).strip()
    build_s = str(build).strip()
    if not _MARKETING_VERSION_RE.fullmatch(version_s):
        raise ValueError(
            f"marketing version must be numeric major.minor[.patch…], got {version!r}"
        )
    if not _BUILD_VERSION_RE.fullmatch(build_s):
        raise ValueError(f"build must be numeric digits, got {build!r}")
    return version_s, build_s


def main(argv: list[str]) -> int:
    if len(argv) == 1 or argv[1] in {"-h", "--help"}:
        print(
            "usage: apps.py ids|choice-re|json|bundle <app>|minos <app>|repo <app>|"
            "listing-name <app> <build>|tag <app> <version> <build>",
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
    if cmd == "retired-bundles":
        print(" ".join(sorted(RETIRED_BUNDLES)))
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
    print(
        "usage: apps.py ids|choice-re|json|bundle <app>|minos <app>|repo <app>|"
        "listing-name <app> <build>|tag <app> <version> <build>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
