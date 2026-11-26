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
        "subtitle": "Experimental builds of Kyro",
        "localized_description": (
            "Kyro Labs is the experimental edition of Kyro, used to try new "
            "features such as upstream Silo updates and additional media "
            "servers before they reach Kyro. It installs separately from Kyro, "
            "keeps its own data and sign-in, and may be less stable. This "
            "unsigned beta requires your own signing and sideloading setup."
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
        "subtitle": "Experimental builds of Kyro for Apple TV",
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
    "kyrox": {
        "bundle": "com.cubbiestream.kyrox",
        "min_os": "18.0",
        "display_name": "Kyro X",
        "platform": "ios",
        "release_repo": "jmargocubs/feather-apps",
        "tag_template": "kyrox-v{version}-b{build}",
        "source_name": "Kyro X",
        "subtitle": "Independent streaming client for Jellyfin and media servers",
        "localized_description": (
            "Kyro X is an independent iOS streaming client featuring local "
            "profiles, direct Jellyfin and Silo media server integration, IPTV "
            "support, and a cinematic playback experience. This unsigned beta "
            "requires your own signing and sideloading setup."
        ),
        "icon_url": "https://jmargocubs.github.io/feather-apps/assets/kyrox/icon.png",
        "tint_color": "#DC2626",
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
