# jmargocubs Apps

App source catalog for the apps that are currently maintained and distributed as
unsigned beta IPAs. Use any signing or sideloading app that reads the standard
`source.json` app-source format.

| Source | URL |
| --- | --- |
| All apps | https://jmargocubs.github.io/feather-apps/source.json |
| Apple TV only | https://jmargocubs.github.io/feather-apps/tvos-source.json |

These URLs are permanent. The repository name is kept so existing sources keep
working; nobody needs to re-add the source.

## Listings

Exactly four active listings (consolidated 2026-11-27):

| Listing | Bundle ID | App ID | Development branch | IPAs hosted in |
| --- | --- | --- | --- | --- |
| Kyro X iOS — Build N | `com.cubbiestream.kyro` | `kyro` | `jmargocubs/Kyro` → `kyro/ios-recovered` | `jmargocubs/Kyro` |
| Kyro X tvOS — Build N | `com.cubbiestream.kyro.tvos` | `kyro-tvos` | `jmargocubs/Kyro` → `kyro/tvos-recovered` | `jmargocubs/Kyro` |
| Zepzi — Build N | `app.flippy.reader` | `zepzi` | `jmargocubs/flippy` → `main` | `jmargocubs/feather-apps` |
| Sunny Meadow — Build N | `com.sunnymeadow.app.beta` | `sunnymeadow` | `jmargocubs/sunnyhill` → `feature/build-50-recovery-polish` | `jmargocubs/feather-apps` |

Kyro X iOS and Kyro X tvOS keep the same bundle IDs as the earlier "Kyro" and
"Kyro Apple TV" listings, so existing installs keep updating in place.

### Retired listings
Kyro X Labs (`com.cubbiestream.kyro.labs`), Kyro Labs Apple TV
(`com.cubbiestream.kyro.tvos.labs`) and the shelved independent Kyro X prototype
(`com.cubbiestream.kyrox`) were removed from the catalog on 2026-11-27. Their
source, tags, GitHub releases and IPA assets are kept; the removed entries are
saved in [docs/retired-listings-20261127.json](docs/retired-listings-20261127.json).
They are listed in `RETIRED_APPS` in `scripts/apps.py`, and `validate_source.py`,
`update_source.py` and the Pages deploy refuse any catalog that contains them.

Listing titles always use **App Name — Build N** for the newest build. Installed
app names come from each IPA and are never rewritten by the catalog. Bundle IDs
never change.

`scripts/apps.py` is the single source of truth for listing names, subtitles,
descriptions, icons, bundle IDs and release tag formats.

## Publishing

- **Local publish (all apps):** a verified IPA is published with
  `scripts/publish_ipa.py`, which uploads the release asset, updates
  `source.json` (and `tvos-source.json` for Apple TV apps), and pushes `main`.

  ```sh
  python3 scripts/publish_ipa.py /absolute/path/to/App.ipa \
    --app kyro-tvos --version 1.0.104 --build 104
  ```

- **Kyro cloud builds:** `jmargocubs/Kyro` → *Publish approved IPA and update
  catalog* runs after a successful *Cloud unsigned IPA* build from an allowed
  Kyro branch and updates the matching Kyro listing.
- Pushing `main` deploys GitHub Pages; *Validate* checks the catalog on every push.

See [docs/release-process.md](docs/release-process.md),
[docs/catalog-listing-names.md](docs/catalog-listing-names.md) and
[docs/nullsign-auto-publish.md](docs/nullsign-auto-publish.md) (historical file
name; the process is signing-app neutral).
