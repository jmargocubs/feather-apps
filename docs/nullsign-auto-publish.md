# Shared source auto-publish policy

Standing authorization for all jmargocubs Apple apps:

**Whenever an IPA is successfully built and verified, publish it automatically
to the GitHub-backed AltStore-compatible source used by signing apps. Do not ask
for a separate publish approval.**

Distribution: AltStore-compatible `source.json` for compatible signing /
sideloading clients.
Repository: [`jmargocubs/feather-apps`](https://github.com/jmargocubs/feather-apps).
Live source: https://jmargocubs.github.io/feather-apps/source.json

Repository listings set `apps[].name` to `App Name — Build N`. Installed app
titles inside IPAs are not modified. See [catalog-listing-names.md](catalog-listing-names.md).

## Covered apps

| App id | Platform | Bundle ID | IPA release host |
|---|---|---|---|
| `kyro` | iOS | `com.cubbiestream.kyro` | `jmargocubs/Kyro` |
| `kyro-tvos` | tvOS | `com.cubbiestream.kyro.tvos` | `jmargocubs/Kyro` |
| `zepzi` | iOS | `app.flippy.reader` | `jmargocubs/feather-apps` |
| `sunnymeadow` | iOS | `com.sunnymeadow.app.beta` | `jmargocubs/feather-apps` |

Future apps are added to `scripts/apps.py`, then published the same way.

## Permanent packaging rule

After a verified unsigned IPA exists:

```sh
cd /path/to/feather-apps
python3 scripts/publish_ipa.py /absolute/path/to/App.ipa \
  --app kyro-tvos --version 1.0.87 --build 87
```

The script:

1. Validates bundle ID, version, build, and minimum OS.
2. Scans for embedded provisioning profiles and secret patterns.
3. Creates or resumes the exact GitHub prerelease (idempotent).
4. Uploads the IPA plus a `.sha256` sidecar.
5. Downloads the public asset without credentials and checks SHA-256/size.
6. Updates `source.json` (and `tvos-source.json` for tvOS) without touching other apps, and sets the listing title to `App Name — Build N` for the published head build.
7. Refuses duplicate mismatched entries and refuses older builds that would downgrade the newest entry. Exact republishes are idempotent and may only refresh a stale listing title.
8. Commits and pushes the catalog update to `feather-apps` `main` (Deploy Pages follows).

If any step fails, the local IPA is left in place for retry. Nothing is deleted.

## Never publish when

- Archive/package verification failed
- Bundle/version/build/minOS metadata mismatches
- Security scan finds provisioning profiles or secret patterns
- The file looks like signing material or private config
- The request would overwrite an unrelated IPA or downgrade an existing newer build

## Preserve

- All other app entries
- Historical version rows already present in the source
- Distinct iOS and tvOS Kyro listings
- Existing GitHub release assets (resume exact matches only)

## Client

Import the source URL in your compatible signing app. Re-sign unsigned IPAs with
your own certificate before install. This workflow does not publish source code,
API keys, provider credentials, provisioning profiles, or signing certificates.
