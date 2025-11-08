# Testing the `release` job (GitHub Actions)

This short guide shows a fast, repeatable way to test the `release` job in CI for `share-and-tell`.

Summary
- The `release` job in `.github/workflows/ci.yml` is configured to run only for tag pushes that start with `v` (for example `v1.2.3`).
- The simplest way to trigger it is to create an annotated git tag locally and push that tag to the repository.

Quick test (recommended)

1. Create an annotated tag locally and push it to origin:

```bash
# create an annotated tag
git tag -a v0.0.1-test -m "Test release v0.0.1-test"
# push the tag to GitHub (this will trigger the workflow)
git push origin v0.0.1-test
```

2. Watch the Actions tab for the new workflow run. The pipeline will:
- run the build jobs (e.g. `windows-x64-package`, `windows-arm64-package`)
- run the `release` job which downloads the artifacts and calls `softprops/action-gh-release@v1` to create a Release.

3. Verify the Release was created:
- Go to the repository `Releases` tab on GitHub and verify a new release named like your tag exists.
- The uploaded release assets should include the artifacts produced by the Windows packaging jobs.

Cleanup (remove the test tag)

If you want to remove the test tag from the remote after verifying:

```bash
# delete the local tag
git tag -d v0.0.1-test
# delete the remote tag
git push origin :refs/tags/v0.0.1-test
```

Notes and troubleshooting
- If the `release` job fails with "GitHub Releases requires a tag", confirm you pushed an actual tag (not just a branch push).
- The `release` job depends on artifacts uploaded by the Windows jobs; if the artifact uploads fail or are missing, the release step may still run but produce an incomplete release.
- If you need to test the release job without creating a persistent tag, use a temporary tag name (as above) and delete it after testing.

Advanced: manual dispatch testing
- You can add `workflow_dispatch` to your workflow to allow manual runs, but the `release` job currently checks `startsWith(github.ref, 'refs/tags/')`, so a manual dispatch will not satisfy that condition unless you also adapt the `if:` condition.

If you want, I can add a short `workflow_dispatch` example and a temporary change to the `if:` condition to enable manual testing; say the word and I'll add it.
