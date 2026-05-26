# Security Policy

## Supported Versions

| Version | Status     |
|---------|------------|
| main    | ✅ Supported |

## Reporting a Vulnerability

Report security vulnerabilities **privately** via GitHub's "Security" tab →
**"Report a vulnerability"**. Do not open public issues for security bugs.

We aim to acknowledge reports within **48 hours** and publish a fix or mitigation
within **7 days** for critical issues.

## Authentication Model

CENTINEL uses a **client-side PBKDF2-SHA256 gate** for the admin panel and
replay viewer. No server-side authentication service is required.

- **Salt**: `centinel-admin-salt-v1`
- **Iterations**: 600 000
- **Hash**: SHA-256 / 256-bit output
- **Storage**: Only hashes are committed to the repository (`web/access.json`).
  Plaintext seeds are **never** stored in version control.
- **Session**: 8-hour token stored in `sessionStorage` (cleared on tab close).

## Cryptographic Integrity

Each data snapshot is hashed with SHA-256 and chained (each hash includes the
previous hash). Optional Bitcoin/OpenTimestamps anchoring provides an external,
tamper-evident proof of existence.

## Scope

- The panel, admin, and replay pages are **static HTML** served via GitHub Pages.
- No secrets, database credentials, or private keys are stored in this repository.
- The `web/access.json` file contains **only PBKDF2 hashes** — not passwords.

## Contact

security@vectis.dev (PGP key available on request)
