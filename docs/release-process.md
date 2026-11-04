# Release Process
1. Validate IPA locally. 2. Create tagged GitHub Release. 3. Upload IPA. 4. Update source.json. 5. Validate. 6. Deploy Pages. 7. Post-deployment check. Rollback: restore previous source.json from git history; never delete historical release assets.

## Operator guide (future releases)
1. Build/test IPA locally.
2. Upload IPA to a draft RC release: gh release create <rc-tag> <ipa> --draft
3. Run workflow "Publish Beta" with app/version/build/rc_tag/expected_sha256/expected_size/release_notes.
4. Approve the release-approval environment gate.
5. Workflow creates tagged release, updates source.json, deploys Pages, verifies.
6. On failure, restore last known-good source.json from git and re-deploy Pages.

## Staging (GitHub Actions artifacts)
Build/test IPA locally, then upload via `gh run upload-artifact` or workflow_dispatch with artifact ID. Record artifact ID, SHA-256, size, bundle, version, build. Draft GitHub Releases are NOT used for staging (unverified privacy). Artifact retention and access controlled by GitHub Actions permissions.

## Approval gate
release-approval environment requires reviewer jmargocubs on main branch. Administrator bypass currently enabled (can_admins_bypass=true). Disabling requires explicit authorization; consequence: even admins must obtain reviewer approval, no self-bypass.

## Rollback
On failure, restore last known-good source.json from git history and redeploy Pages. Never delete historical release assets.
