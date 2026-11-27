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

| Listing | Bundle ID | Role | IPAs hosted in |
| --- | --- | --- | --- |
| Kyro — Build N | `com.cubbiestream.kyro` | Main Kyro iPhone app (recent builds show "Kyro X" on the Home Screen) | `jmargocubs/Kyro` |
| Kyro Apple TV — Build N | `com.cubbiestream.kyro.tvos` | Main Kyro Apple TV app (approved tvOS line) | `jmargocubs/Kyro` |
| Kyro X Labs — Build N | `com.cubbiestream.kyro.labs` | Experimental Kyro iPhone builds, separate install | `jmargocubs/Kyro` |
| Kyro Labs Apple TV — Build N | `com.cubbiestream.kyro.tvos.labs` | Experimental Kyro Apple TV builds, separate install | `jmargocubs/Kyro` |
| Kyro X — Build N | `com.cubbiestream.kyrox` | Independent Kyro X rebuild, separate app | `jmargocubs/feather-apps` |
| Zepzi — Build N | `app.flippy.reader` | Comic reader for Komga | `jmargocubs/feather-apps` |
| Sunny Meadow — Build N | `com.sunnymeadow.app.beta` | Mood check-ins and recovery journaling | `jmargocubs/feather-apps` |

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
