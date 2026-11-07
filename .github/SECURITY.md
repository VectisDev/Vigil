# Security Policy

One person maintains this repository, under the pseudonym VectisDev.
There is no security team, no on-call rotation, and no organization behind the inbox.

## Supported versions

No release tag has been published. Security fixes land on the default branch, `main`.
When a tag exists, only `main` and the latest tag are in scope. Older tags are not supported.

The version string in `pyproject.toml` is `0.1.0`. Publishing that tag is a separate maintainer action (`.github/workflows/release.yml`, documented in `docs/operations/RELEASE.md`). This policy does not claim the tag exists.

## Reporting a vulnerability

Report privately, in one of these two places:

1. [GitHub private vulnerability reporting](https://github.com/VectisDev/Vigil/security/advisories/new)
2. Email: vectisdev26@proton.me

Do not open a public issue for a security bug. There is no other contact address.

No public encryption key is in this repository. Do not describe one as available on request.
To publish one later, add the fingerprint to this section and commit the public key as `docs/security/vectisdev.asc`.
Until that file exists, use one of the two channels above. The mailbox is not encrypted to a key this repository publishes.

## What one maintainer can promise

Reports are read when that person next checks the advisory inbox and vectisdev26@proton.me.
The intended interval is within 14 days. Illness, travel, or a missed week can make it longer.
There is no 48-hour acknowledgement and no fixed number of days in which a fix is promised.

A confirmed issue that lets someone change published evidence, push to `main`, or take the repository is handled before feature work.
If a fix will not land soon, the maintainer posts a short mitigation note on the advisory.
Everything else waits for the next change.

## Scope

In scope: the source in this repository, the GitHub Actions workflows, and the static site under `web/`.

Out of scope: the electoral authority's portal, secrets on a fork, and social engineering of the maintainer.
The software records what a portal published. It does not decide why a number changed.

## What the code actually does

- A capture is linked with SHA-256 only when the pipeline writes `previous_hash`. The bundled Honduras 2025 files do not have that field. `verify/verify_chain.py` exits 1 on them. See `docs/evidence/HN2025.md`.
- A Merkle root can be anchored with OpenTimestamps when a proof file was actually created. The proof next to the 2025 sample commits to that root. It is not continuous custody during the count.
- Ed25519 signing exists in the code. Private keys are not in this repository. No witness set is operating from this tree.
- The operator panel (`web/ops/`, `web/replay/`) is static HTML on GitHub Pages. The access check is a convenience, not a boundary: the page and its data are public. `web/access.json` stores key hashes only (SHA-256 in the published format; an older local wizard wrote PBKDF2-SHA256). Plaintext keys are not committed. The browser session lasts 8 hours in `sessionStorage`.
- The local API checks `X-Vigil-Key` (the older `X-Centinel-Key` is still accepted) in constant time. Changing the repository on GitHub requires a token with that permission.

## Secrets

- Do not commit tokens, private keys, passwords, or plaintext panel keys.
- GitHub Actions secrets stay in the repository settings. Workflows pass them as environment variables. They are not printed.
- `scripts/encrypt_secrets.py` can encrypt a local env file. Ciphertext in git is still a secret in git. This repository does not store an encrypted signing key or an Arbitrum key. Arbitrum stays off unless an operator sets `ARBITRUM_PRIVATE_KEY` outside the tree.
- `web/access.json` holds hashes only.

## Workflow permissions

The default `GITHUB_TOKEN` in `.github/workflows/` is `contents: read`.
A job that pushes commits or publishes a release sets `contents: write` on that job.
A reusable gate job sets `contents: read`.
`pull_request_target` is not used.
The Scorecard job may set `id-token: write` and `security-events: write`. It does not add a badge to the README.

## What is configured, and what is not

- CodeQL runs from `.github/workflows/codeql.yml` on push, on pull request, and on a weekly schedule.
- Dependabot is configured in `.github/dependabot.yml` (weekly; pip, Poetry, and GitHub Actions).
- Secret scanning and push protection are GitHub settings. This file does not say they are on. The maintainer checks that in the repository settings.
- OpenSSF Scorecard runs from `.github/workflows/scorecard.yml` and uploads SARIF. That run is not a passed audit.
- No third-party security audit has been completed. `docs/audits/SECURITY_AUDIT.md` and `docs/security/SECURITY-REVIEW.md` are the maintainer's own notes.

## Other documents

`docs/security/SECURITY-POLICY.md` and `docs/compliance/SECURITY_POLICY.md` point here.
If they disagree with this file, this file wins.
