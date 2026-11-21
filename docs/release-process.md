# Beta release process

## Preferred path: shared source auto-publish

Standing policy: after a verified unsigned IPA build succeeds, publish immediately with
`scripts/publish_ipa.py`. Do not wait for a separate approval prompt. Full policy:
[nullsign-auto-publish.md](nullsign-auto-publish.md). Listing titles:
[catalog-listing-names.md](catalog-listing-names.md).

```sh
cd /path/to/feather-apps
python3 scripts/publish_ipa.py /absolute/path/to/App.ipa \
  --app kyro-tvos --version 1.0.0 --build 87
```

Supported app ids: `kyro`, `kyro-tvos`, `zepzi`, `sunnymeadow`.

## Marketing version and build

Marketing version (`CFBundleShortVersionString` / catalog `version`) and build
number (`CFBundleVersion` / catalog `buildVersion`) are independent. Pass the
IPA’s real marketing version and build to `publish_ipa.py`; do not rewrite the
marketing string to embed the build. Repository listing titles carry the build
as `App Name — Build N`. Historical `versions[]` rows and release URLs stay
unchanged.

## Legacy Actions path: stage / validate / publish

The `Publish Beta` workflow has three explicit operations: `stage`, `validate`, and `publish`.
The IPA is never committed to Git. Staging uses documented GitHub interfaces: the local helper
calls the supported `gh release create --draft` flow to upload an authenticated **draft** release
asset, then calls
`gh workflow run` to dispatch `Publish Beta` in `stage` mode. The runner verifies those exact
bytes, creates a seven-day immutable Actions artifact with `actions/upload-artifact`, and deletes
the temporary draft release. A draft must never be published.

For day-to-day packaging sessions, prefer `publish_ipa.py`. The Actions path remains available
for audited CI-only releases.

## One-time authentication setup

1. Authenticate the GitHub CLI as a repository administrator: `gh auth login`.
2. Ensure repository workflow permissions allow PR creation:
   **Allow GitHub Actions to create and approve pull requests** enabled.
3. The automated source-update branch and PR use the built-in `GITHUB_TOKEN` with
   explicit `contents: write` and `pull-requests: write` permissions. No external
   GitHub App, key generation, or secret configuration is required.
4. Source validation and test suites run explicitly prior to committing the updated catalog,
   and validate upon merge to `main`.

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

```

The validation job independently runs the one-IPA, metadata, security, checksum, and size checks.
The publishing job repeats all validations, creates or resumes the release, downloads the public IPA
without credentials, verifies the exact SHA-256 and size, and updates source.json and tvos-source.json
directly on main. Pushing to main triggers **Deploy Pages**, which retries network, malformed, and
successful-but-stale JSON responses for up to five minutes.

## Fully automated publishing

The release pipeline runs hands-off without manual review gates or PR approvals. All automated
integrity validations, bundle checks, OS version checks, security scans, downgrade protections,
and public download verifications remain strictly enforced on every release.

## Recover after a partial publish

Re-run the exact publish command with the same version, build, artifact run ID, artifact name,
SHA-256, size, and release notes:

```sh
gh workflow run publish-beta.yml --ref main \
  -f operation=publish -f app=kyro -f version=1.0.0 -f build=22 \
  -f artifact_run_id=RUN_ID -f artifact_name=kyro-ipa-candidate \
  -f expected_sha256=SHA256 -f expected_size=SIZE_BYTES \
  -f release_notes='Approved beta notes'
```

If the public tag already exists, the workflow does not modify it. It requires exactly one IPA
asset with the expected name, uploaded state, size, digest when GitHub supplies one, downloaded
SHA-256, and app metadata. It then resumes public-asset verification and source-update PR creation.
An exact source entry or matching open PR is treated as success; a matching closed PR is reopened.
Any existing release, source entry, or recovery branch that differs from the approved values is
rejected without overwriting or deleting it.

## Rollback

Restore the last known-good `source.json` through a normal PR and redeploy Pages. Never delete or
replace an existing public release asset. A failed staging helper deletes its temporary draft when
possible; if interrupted, delete the still-draft `staging-*` release with authenticated GitHub UI
or API access, and never publish it.


## Sunny Meadow

Sunny Meadow uses the same stage → validate → publish flow. App id is `sunnymeadow`,
bundle id is `com.sunnymeadow.app.beta`, and minimum iOS is `17.0`.

```sh
cd /path/to/feather-apps
python3 scripts/stage_ipa.py /absolute/path/to/SunnyMeadow-v0.3.9-b9-beta-unsigned.ipa \
  --app sunnymeadow --version 0.3.9 --build 9
```

Then validate and publish with `app=sunnymeadow`, the printed artifact run id / name,
SHA-256, and size. The source-update PR preserves Kyro and Zepzi entries.
