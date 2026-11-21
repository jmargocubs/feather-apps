# Catalog listing titles (`apps[].name`)

## Which field source clients show

Compatible AltStore-style source clients use the **app object `name`** field as
the title in the repository / source listing.

Verified against this repository’s live `source.json` schema:

- Listing title: `apps[].name`
- Bundle identity: `apps[].bundleIdentifier` (unchanged by listing titles)
- Installable builds: `apps[].versions[]` (`version`, `buildVersion`, `downloadURL`, …)

The installed SpringBoard / home-screen name comes from the IPA
(`CFBundleDisplayName` / related Info.plist keys). Publishing never rewrites IPA
payloads, so the on-device app title stays the original product name.

## Generated format

```text
{source_name} — Build {buildVersion}
```

Examples:

- `Kyro — Build 101`
- `Kyro Apple TV — Build 101`
- `Zepzi — Build 1`
- `Sunny Meadow — Build 48`

`source_name` is the stable product stem from `scripts/apps.py`. The em dash
(`—`, U+2014) is intentional.

## Behavior

- On each catalog update, `scripts/update_source.py` sets `apps[].name` from the
  **current head** version row (`versions[0]` after insert).
- Historical `versions[]` rows are preserved; only the listing title moves forward.
- Idempotent republishing of the same build refreshes a stale listing title when
  the release row already matches, then no-ops on exact repeat.
- Feed URLs (`source.json`, `tvos-source.json`) are not renamed.

## App-specific display limitations

| Surface | Limitation |
|---|---|
| Repository listing | Shows `apps[].name` (includes build). Long names may truncate in narrow UI cells depending on the client. |
| Version history UI | Clients typically show marketing `version` and `buildVersion` per row; they do not need a per-version copy of the listing title. Marketing version and build stay independent (for example `1.0.0` + build `105`). |
| Home screen after install | Still the IPA’s own display name (for example `Kyro`), not `Kyro — Build N`. |
| tvOS vs iOS sources | Apple TV builds also appear in `tvos-source.json`; iOS `source.json` may still list Kyro Apple TV for multi-app sources. |
| Client variance | Some third-party clients may prefer subtitle/version chips over the listing title. The AltStore-compatible field for the list title remains `name`. |

## Refresh without a new IPA

```sh
python3 scripts/update_source.py --source source.json --refresh-listing-names
python3 scripts/update_source.py --source tvos-source.json --refresh-listing-names
python3 scripts/validate_source.py source.json
python3 scripts/validate_source.py tvos-source.json
```
