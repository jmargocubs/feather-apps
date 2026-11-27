# Publishing (all four active apps) — current policy (2026-11-27)

**Builds start manually. A build publishes only when it is approved for
distribution; then it publishes automatically** — GitHub Release + existing
catalog entry, with no further manual steps. Unapproved builds are never
published.

Every path below runs the same publisher, `scripts/publish_ipa.py`, so release
tag, title, notes, IPA asset name, download URL, catalog entry and the
"App — Build N" listing name are identical whichever environment you use
(enforced by `tests/test_publish_parity.py`).

| App (id) | Listing | Local Mac | GitHub Actions (build + publish) |
|---|---|---|---|
| `kyro` | Kyro X iOS — Build N | build with the Kyro package script, then `publish_ipa.py --approved` | Kyro → *Cloud unsigned IPA* (platform `ios`, ref `kyro/ios-recovered`) with **publish_approved ✓** → *Publish approved IPA and update catalog* runs automatically |
| `kyro-tvos` | Kyro X tvOS — Build N | same, `--app kyro-tvos` | same, platform `tvos`, ref `kyro/tvos-recovered` |
| `zepzi` | Zepzi — Build N | build, then `publish_ipa.py --app zepzi --approved` | flippy → *Build Unsigned iOS Beta IPA* (manual) on `main` with **publish_approved ✓** |
| `sunnymeadow` | Sunny Meadow — Build N | build, then `publish_ipa.py --app sunnymeadow --approved` | sunnyhill → *Build Unsigned iOS Beta IPA* (manual) on `main` or the active development branch with **publish_approved ✓** |

An already-built IPA can also be published from GitHub with feather-apps
*Publish Beta* (`stage` → `validate` → `publish` with **publish_approved ✓**).
For Kyro apps that path needs a `KYRO_PUBLISH_TOKEN` secret in feather-apps.

## The approval gate
- Local: `publish_ipa.py` without `--approved` only validates and prints the exact
  plan (including the catalog entry), then exits 3 — nothing is uploaded or pushed.
- Actions: every workflow has a `publish_approved` checkbox (default off). Off =
  build/validate only.
- Only tick the box / pass `--approved` for a build that is approved for distribution.

## Shared rules (apps.py)
- Tag: `kyro-ios-v{V}-build{B}-rc1`, `kyro-tvos-v{V}-build{B}-rc1`, `zepzi-v{V}-b{B}`, `sunnymeadow-v{V}-b{B}`
- Asset: `Kyro-iOS-v{V}-Build{B}-Unsigned.ipa`, `Kyro-tvOS-v{V}-Build{B}-Unsigned.ipa`,
  `Zepzi-v{V}-b{B}-unsigned.ipa`, `SunnyMeadow-v{V}-b{B}-beta-unsigned.ipa` (input file name doesn't matter)
- Title: `{App} {V} (Build {B}) Beta`; standard notes + optional extra notes; prerelease
- Version: numeric version and build; Kyro X iOS/tvOS also require `major.minor.{B}`
- Release repo: Kyro apps → `jmargocubs/Kyro` (tag targets the source commit); Zepzi / Sunny Meadow → `jmargocubs/feather-apps`
- Catalog: existing entry by bundle ID; retired listings are refused

## Plan-only check (no upload)
```sh
python3 scripts/publish_ipa.py /path/to/App.ipa --app kyro --version 1.0.140 --build 140
```
