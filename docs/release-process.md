# Beta release process

The `Publish Beta` workflow has three explicit operations: `stage`, `validate`, and `publish`.
The IPA is never committed to Git. Staging uses documented GitHub interfaces: the local helper
calls the supported `gh release create --draft` flow to upload an authenticated **draft** release
asset, then calls
`gh workflow run` to dispatch `Publish Beta` in `stage` mode. The runner verifies those exact
bytes, creates a seven-day immutable Actions artifact with `actions/upload-artifact`, and deletes
the temporary draft release. A draft must never be published.

## One-time authentication setup

1. Authenticate the GitHub CLI as a repository administrator: `gh auth login`.
2. Create a GitHub App installed only on `jmargocubs/feather-apps`, with repository permissions
   **Contents: Read and write** and **Pull requests: Read and write**. No organization permissions,
   administration permission, or webhooks are required.
3. Store its App ID as the Actions secret `SOURCE_UPDATE_APP_ID` and its private key as
   `SOURCE_UPDATE_APP_PRIVATE_KEY`.

The source-update branch and PR use a short-lived installation token from that app. They do not
use `GITHUB_TOKEN`: the repository currently has "Allow GitHub Actions to create and approve pull
requests" disabled. The App token also causes normal pull-request workflows to run.

## Stage from the Mac

```sh
cd /path/to/feather-apps
python3 scripts/stage_ipa.py /absolute/path/to/Kyro.ipa \
  --app kyro --version 1.0.0 --build 22
```

The helper prints JSON. Record `artifact_run_id`, `artifact_name`, `ipa_sha256`, and `ipa_size`.
The exact workflow name is **Publish Beta** and the staging operation is `stage`. To test a branch
before merge, add `--ref feature/release-pipeline`; normal operation uses the default `--ref main`.

## Validate without publishing

```sh
gh workflow run publish-beta.yml --ref main \
  -f operation=validate -f app=kyro -f version=1.0.0 -f build=22 \
  -f artifact_run_id=RUN_ID -f artifact_name=kyro-ipa-candidate \
  -f expected_sha256=SHA256 -f expected_size=SIZE_BYTES
```

This is the safe cross-run integration check. The validation job has explicit `actions: read`,
downloads the named artifact from the explicit run, requires exactly one IPA, and verifies bundle
ID, version, build, minimum OS, security scan, SHA-256, and size.

## Publish after review

```sh
gh workflow run publish-beta.yml --ref main \
  -f operation=publish -f app=kyro -f version=1.0.0 -f build=22 \
  -f artifact_run_id=RUN_ID -f artifact_name=kyro-ipa-candidate \
  -f expected_sha256=SHA256 -f expected_size=SIZE_BYTES \
  -f release_notes='Approved beta notes'
```

The validation job runs before the `release-approval` environment gate. The publishing job has
its own explicit `actions: read` permission and independently repeats the one-IPA, metadata,
security, checksum, and size checks. It then creates the public release, downloads the public IPA
without credentials and verifies the exact SHA-256 and size, and opens a source-update PR using
the GitHub App token. Merge that PR normally; it triggers **Deploy Pages**, which retries network,
malformed, and successful-but-stale JSON responses for up to five minutes.

## Current repository controls

The `release-approval` environment requires reviewer `jmargocubs` and currently has administrator
bypass disabled (`can_admins_bypass=false`). No main-branch protection rule or ruleset is currently
configured; the workflow still uses a PR and never pushes `source.json` directly to `main`.

## Rollback

Restore the last known-good `source.json` through a normal PR and redeploy Pages. Never delete or
replace an existing public release asset. A failed staging helper deletes its temporary draft when
possible; if interrupted, delete the still-draft `staging-*` release with authenticated GitHub UI
or API access, and never publish it.
