#!/usr/bin/env python3
import argparse
import json


def validate_release(release, tag, asset, sha256, size):
    if release.get("tag_name") != tag:
        raise ValueError(f"release tag mismatch: {release.get('tag_name')!r}")
    if release.get("draft") is not False:
        raise ValueError("release must be public, not draft")
    assets = release.get("assets", [])
    ipa_assets = [item for item in assets if item.get("name", "").lower().endswith(".ipa")]
    if len(ipa_assets) != 1:
        raise ValueError(f"expected exactly one IPA asset, found {len(ipa_assets)}")
    candidate = ipa_assets[0]
    if candidate.get("name") != asset:
        raise ValueError(f"release asset mismatch: {candidate.get('name')!r}")
    if candidate.get("state") != "uploaded":
        raise ValueError(f"release asset is not uploaded: {candidate.get('state')!r}")
    if candidate.get("size") != size:
        raise ValueError(f"release asset size mismatch: {candidate.get('size')!r}")
    digest = candidate.get("digest")
    if digest is not None and digest != f"sha256:{sha256}":
        raise ValueError(f"release asset digest mismatch: {digest!r}")
    url = candidate.get("browser_download_url")
    if not url:
        raise ValueError("release asset has no browser download URL")
    return url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release_json")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--size", required=True, type=int)
    args = parser.parse_args()
    with open(args.release_json, encoding="utf-8") as handle:
        release = json.load(handle)
    url = validate_release(release, args.tag, args.asset, args.sha256, args.size)
    print(f"release metadata verified: {url}")


if __name__ == "__main__":
    main()
