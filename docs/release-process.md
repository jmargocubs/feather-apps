# Release Process
1. Validate IPA locally. 2. Create tagged GitHub Release. 3. Upload IPA. 4. Update source.json. 5. Validate. 6. Deploy Pages. 7. Post-deployment check. Rollback: restore previous source.json from git history; never delete historical release assets.

## Operator guide (future releases)
1. Build/test IPA locally.
2. Upload IPA to a draft RC release: gh release create <rc-tag> <ipa> --draft
3. Run workflow "Publish Beta" with app/version/build/rc_tag/expected_sha256/expected_size/release_notes.
4. Approve the release-approval environment gate.
5. Workflow creates tagged release, updates source.json, deploys Pages, verifies.
6. On failure, restore last known-good source.json from git and re-deploy Pages.
