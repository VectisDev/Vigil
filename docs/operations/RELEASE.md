# Software release

Daily tags named `forensic-*` are data exports. They are not software releases.

A software release is a tag `vX.Y.Z` that matches `tool.poetry.version` in `pyproject.toml`, with a source tarball, a CycloneDX SBOM, `SHA256SUMS`, and a keyless signature over `SHA256SUMS`.

This repository does not create that tag by itself. The maintainer runs one command after the version in `pyproject.toml` is the version they want to publish:

```bash
gh workflow run release.yml --ref main -f version=v0.1.0
```

`v0.1.0` is the example that matches the version in the tree today. If `pyproject.toml` says `0.1.0`, the workflow rejects any other tag. It also refuses to replace a tag that already exists.

What the workflow does, and only when that command is run:

1. Checks out `main` at the commit GitHub Actions starts from.
2. Builds `vigil-<version>.tar.gz` with `git archive`.
3. Writes `sbom.cdx.json` from `requirements.txt` with `cyclonedx-py`.
4. Writes `SHA256SUMS` for the tarball and the SBOM.
5. Signs `SHA256SUMS` with keyless cosign (GitHub OIDC). No long-term signing key is stored in the repo.
6. Creates the git tag and a GitHub release carrying those four files.

Check a published release locally, after one exists:

```bash
cosign verify-blob \
  --certificate SHA256SUMS.pem \
  --signature SHA256SUMS.sig \
  --certificate-identity-regexp '^https://github.com/VectisDev/Vigil/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  SHA256SUMS
sha256sum -c SHA256SUMS
```

Do not run the workflow from this change set until you intend to publish `v0.1.0`.
