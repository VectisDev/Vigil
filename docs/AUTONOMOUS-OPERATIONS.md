---
Version: 1.0
Date: 2026-05-20
Status: Active
Audience: Grant evaluators · OTF · NED · NDI · IRI · Mozilla Foundation · Carter Center
---

# Autonomous Operations Capability

> **ES:** Qué hace el sistema por su cuenta, qué requiere intervención humana y por qué eso importa.  
> **EN:** What the system does autonomously, what requires human intervention, and why that matters.

---

## The core claim

Centinel can monitor a national election from fork to final report with **a single human action at setup**: creating a GitHub Personal Access Token. Everything else — infrastructure provisioning, endpoint discovery, data capture, cryptographic chaining, anomaly detection, failure recovery, and public data publication — runs without operator intervention.

This is verifiable. Every claim below maps to a specific file and workflow in this repository.

---

## Phase 1 — Fork and deployment (≤ 10 minutes, 1 human action)

### What the system does automatically

| Action | Implementation | Trigger |
|--------|---------------|---------|
| Detects new fork environment | `setup-wizard.yml` state check | First push to `main` |
| Opens GitHub Issue with exact setup instructions | `setup-wizard.yml` → `github-script` | Token missing |
| Provides direct links to token creation page (pre-scoped) | Issue body with `?scopes=repo` URL | Token missing |
| Retries hourly if operator added token but forgot to re-run wizard | `schedule: '0 * * * *'` | Always |
| Creates `centinel-data` public repo via GitHub API | `setup-wizard.yml` → curl POST | Token present, repo absent |
| Initializes directory structure in `centinel-data` | `push_file()` calls in wizard | Repo just created |
| Deploys IPFS-pin and weekly-backup workflows to `centinel-data` | `push_file()` calls in wizard | Repo just created |
| Enables GitHub Pages via API | `setup-wizard.yml` → curl POST | Setup complete |
| Opens fallback Issue if Pages auto-enable fails | `github-script` with deduplication | Pages API returns non-2xx |
| Updates README with real links to data repo and panel | `sed` + `git commit` in wizard | Setup complete |
| Transforms fork README from "deploy guide" to "live instance" | Python regex replace in wizard | Setup complete |
| Closes setup Issue automatically | `github-script` on `state=ready` | Token + repo verified |

### What requires a human

**One action: creating a GitHub Personal Access Token.**

GitHub's security policy prohibits any external system from creating tokens on behalf of a user. This is not a limitation of Centinel — it is a GitHub platform constraint with no exception. The wizard opens an Issue with a direct link to the pre-scoped token creation page. The operator clicks, copies, pastes. That is the full extent of required human action for a standard deployment.

---

## Phase 2 — Endpoint discovery (automated, adversary-aware)

Electoral authorities frequently use Angular or React SPAs that construct API URLs at runtime — invisible in source code. Centinel handles this in two layers:

### Layer 1 — Static analysis
Scans JavaScript bundles and page source for URL patterns matching known electoral API structures. Fast, zero dependencies.

### Layer 2 — Playwright fallback (headless browser)
If static analysis returns zero valid candidates, launches a headless Chromium instance, navigates to the electoral authority URL, and intercepts all XHR/fetch responses in real time. Captures whatever the application actually requests, regardless of how URLs are constructed.

### Validation (Honduras CNE case study)
Each candidate endpoint is validated against:
- Numeric department code in URL path (`/01-/` = Atlántida, `/00-/` = national aggregate, codes 01–18 alphabetically)
- Department field in JSON payload (`departamento`, `department`, `depto` keys)
- Cross-check: if URL says Atlántida and payload says Islas de la Bahía, the candidate is rejected

This prevents a class of silent errors where the system captures a valid endpoint for the wrong geographic unit.

**Implementation:** `centinel_engine/cne_endpoint_healer.py` — `DEPARTMENT_CODE_MAP`, `_discover_via_playwright()`, `_validate_candidates()`

---

## Phase 3 — Continuous capture and cryptographic chaining

### Capture cadence
- `scheduler.yml`: every 15 minutes
- `audit.yml`: every 3 hours (configurable to 30 minutes for election night via `workflow_dispatch` input)

### Cryptographic guarantees per snapshot
- SHA-256 hash of each data file
- Merkle root across all files in the snapshot
- Hash chain: each snapshot includes the hash of the previous snapshot
- OpenTimestamps anchor in Bitcoin (no cost, no trusted third party)

These properties together mean: **any observer can verify, offline, that a specific snapshot existed at a specific time and has not been modified since publication.** No institutional trust required.

### Anomaly detection (automated)
- Benford's Law analysis on vote counts
- Statistical deviation detection between consecutive snapshots
- Cross-witness comparison (when federation is active)
- Results published automatically to `centinel-data` and the visualization panel

---

## Phase 4 — Defense under adversarial conditions

The system applies layered defense with automatic mode escalation. No operator action required until the system explicitly requests it.

### Automatic escalation

| Failures | Mode | Capture interval | Action |
|----------|------|-----------------|--------|
| 0–1 | NORMAL | 30 min | Standard operation |
| 2–3 | CAUTION | 20 min | Increased frequency |
| 4+ | SURVIVAL | 10 min | Maximum resilience |

### Specific threats handled automatically

| Threat | Response | Implementation |
|--------|----------|---------------|
| Endpoint temporarily unreachable | Circuit breaker opens; closes automatically on recovery | `cne_endpoint_healer.py` |
| Selective blocking by IP pattern | Non-deterministic jitter in capture intervals | `download_and_hash.py` |
| Man-in-the-middle / traffic interception | ChaCha20-Poly1305 encryption in transit | `core/advanced_security.py` |
| Local state manipulation | Auto-resync from replicas before resuming | `air_gap()` mechanism |
| Active compromise detected | Honeypot trigger → freeze → backup → integrity check → resume | `air_gap()` mechanism |
| Endpoint URL changes | Healer re-discovers from base URL on next cycle | `cne_endpoint_healer.py` |

---

## Phase 5 — Infrastructure failure recovery

### git push failure in `audit.yml`

Three-attempt recovery chain, fully automatic:

1. **Normal rebase** — standard git pull --rebase + push
2. **fetch + hard-reset + recommit** — discards the merge conflict, applies the captured snapshot on top of `origin/main`, pushes
3. **force-with-lease** — snapshot takes precedence, no data loss

If all three fail: workflow exits with code 0 (never goes red), snapshot is safe on disk, next cycle retries automatically. A `centinel-git-error` Issue opens with exact diagnosis and manual fix commands. It closes automatically when the next cycle succeeds.

### Token expiry (401/403)

Detected by the wizard on every hourly cycle. On detection:
1. Sends push notification via ntfy.sh if `CENTINEL_NTFY_TOPIC` is configured
2. Opens `centinel-token-error` Issue with direct link to Classic PAT creation page and direct link to Secrets settings
3. Includes explicit warning about Fine-grained PAT incompatibility (silent failure mode)
4. Closes the Issue automatically when the token is valid again

**Deduplication:** the system checks for an existing open Issue with the same label before creating a new one. Running the wizard 10 times with an expired token produces exactly 1 open Issue.

### GitHub Actions outage

If GitHub Actions is unavailable, the system cannot self-recover — it has no execution environment. Three local fallback options are documented in `docs/EMERGENCY-PROCEDURES.md`, each requiring a single command:

```bash
# Option 1 — Docker Compose
docker-compose up -d centinel-engine centinel-watchdog

# Option 2 — Python + system cron
echo "*/15 * * * * cd /path && python -m scripts.download_and_hash" | crontab -

# Option 3 — CLI
poetry run centinel cron --interval 15m
```

Data captured locally syncs to `centinel-data` automatically when Actions recovers.

---

## Phase 6 — Data publication and resilience

### Automatic publication chain

```
capture → centinel-engine/data/
        → push to centinel-data/snapshots/  (each cycle)
        → IPFS pin via Pinata               (each push, if PINATA_JWT configured)
        → weekly GitHub Release archive     (every Sunday 3am UTC)
```

Each layer adds a redundancy tier:
- `centinel-data`: public GitHub repo, forkable by any observer
- IPFS: censorship-resistant, survives GitHub takedown
- GitHub Releases: versioned archive with SHA-256 manifest

### Verification without running Centinel

Any third party — NDI, Carter Center, a journalist, a citizen — can verify the data without installing anything:

```bash
git clone https://github.com/OPERATOR/centinel-data.git
sha256sum centinel-data/snapshots/TIMESTAMP/results.json
# Compare with published hash in centinel-data/hashes/TIMESTAMP.sha256
```

The cryptographic chain is self-contained in the data repository.

---

## What requires human intervention — complete list

This section is exhaustive. If it is not listed here, the system handles it autonomously.

| Situation | Why it cannot be automated | Mitigation |
|-----------|---------------------------|------------|
| Creating a GitHub PAT | GitHub platform security policy. No API exists for this. | Wizard opens Issue with direct pre-scoped link. One click, one copy-paste. |
| Renewing an expired token | Same reason | Wizard detects 401/403, opens Issue with direct link, sends ntfy alert |
| Endpoints behind authentication | Cannot authenticate without credentials; even with credentials, session tokens rotate | Document in `SETUP-GUIDE.md` §9: manual DevTools discovery + config paste |
| Endpoint architecture completely redesigned by authority | Healer re-discovers from base URL, but needs the new base URL | Operator re-runs wizard with new URL |
| GitHub Actions fully unavailable | No execution environment | Three documented one-command local fallbacks |
| Election night cadence (audit.yml) | Cron cannot change itself dynamically | `election_mode` input in workflow_dispatch, or edit cron line and push |
| P2P federation peer discovery | No automatic peer registry exists | Operators register peers manually |
| Public escalation | Editorial and political judgment | Operator decides when and how to communicate findings |
| Academic validation | Requires institutional engagement | UPNFM partnership in progress (see `docs/ACADEMIC_ACCESS.md`) |

---

## What this means operationally

A civil society organization with no technical staff can:

1. Fork the repository
2. Follow one Issue (create a token, paste it)
3. Run the wizard once with the electoral authority URL
4. Leave it running

The system captures, verifies, and publishes data for the full electoral cycle. If something breaks, it either fixes itself or opens an Issue explaining exactly what to do. The operator does not need to monitor logs, check dashboards, or intervene unless explicitly notified.

**This is not a claim about the political impact of the tool.** It is a precise statement about operational burden: one person, one afternoon of setup, zero ongoing technical maintenance under normal conditions.

---

## Current limitations (honest assessment)

- **v0.1 pre-pilot.** Core cryptographic engine is stable and tested (499 passing tests). Field validation with real electoral data is pending (2–3 municipalities, Honduras, target Q3 2026).
- **Authenticated endpoints** are not yet handled automatically. Planned for v0.2 with Playwright credential injection.
- **Fine-grained PAT incompatibility** with GitHub API v3 is a current footgun. The wizard warns explicitly; Classic PAT requirement is documented.
- **Academic validation** is in progress at UPNFM (Honduras). No independent peer review yet.
- **Federation** is architecturally designed but not field-tested with multiple independent operators.

---

## References

- [ARCHITECTURE.md](ARCHITECTURE.md) — cryptographic theorems T1–T4 and system design
- [SECURITY-REVIEW.md](SECURITY-REVIEW.md) — threat model and dependency audit
- [METHODOLOGY.md](METHODOLOGY.md) — statistical detection methods
- [EMERGENCY-PROCEDURES.md](EMERGENCY-PROCEDURES.md) — local fallback procedures
- [OPERATOR-RUNBOOKS.md](OPERATOR-RUNBOOKS.md) — ntfy.sh setup and auto-Issue reference
- [SETUP-GUIDE.md](SETUP-GUIDE.md) — full wizard documentation including authenticated endpoints
- [DATA-REPOS.md](DATA-REPOS.md) — code/data separation architecture
- [BUDGET_NARRATIVE.md](BUDGET_NARRATIVE.md) — OTF grant narrative ($95K / 12 months)
