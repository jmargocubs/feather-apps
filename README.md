# jmargocubs Apps

Public beta distribution source for **Kyro (iOS)**, **Kyro Apple TV (tvOS)**,
**Zepzi**, and **Sunny Meadow**.

Primary client: **Nullsign** (AltStore-compatible source format).

Source URL: https://jmargocubs.github.io/feather-apps/source.json

Apple TV-only source: https://jmargocubs.github.io/feather-apps/tvos-source.json

IPAs are hosted on GitHub Releases (`jmargocubs/Kyro` for Kyro iOS/tvOS;
`jmargocubs/feather-apps` for Zepzi and Sunny Meadow). Builds are unsigned;
testers re-sign with their own certificate before install.

## Auto-publish policy

A successful verified IPA build automatically publishes through
`scripts/publish_ipa.py`. No separate publish approval is required. See
[docs/nullsign-auto-publish.md](docs/nullsign-auto-publish.md).

```sh
python3 scripts/publish_ipa.py /absolute/path/to/App.ipa \
  --app kyro-tvos --version 1.0.0 --build 87
```
