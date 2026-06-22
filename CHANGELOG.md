# Changelog — Centinel Engine

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.2.0] — 2026-05-18

### Added
- `scripts/validate_false_positive_rate.py` — reproducible FP validation (500 iterations, 1,500 snapshots)
- `docs/fp_results_500.json` — machine-readable FP results (seed=42)
- `.github/workflows/observer_pack.yml` — CI auto-generates observer pack ZIP on push
- `scripts/setup_wizard.py` — interactive bilingual onboarding wizard
- `scripts/centinel_service.sh` — PID-based service manager (start/stop/restart/status/logs)
- `observer_pack/README.md` — single entry point for OTF / Carter Center / EU EOM evaluators
- `docs/BUDGET_NARRATIVE.md` — bilingual OTF grant budget narrative ($95K / 12 months)
- `docs/FALSE_POSITIVE_ANALYSIS.md` — validated FP rates for all 15 rules

### Changed
- All `docs/` filenames standardized to `UPPER-SNAKE-CASE.md` international convention
- `docs/README.md` rewritten as comprehensive bilingual navigation index (59 documents)
- `docs/FALSE_POSITIVE_ANALYSIS.md` updated to 500 iterations with tight Wilson CIs
- Pydantic V2 migration complete across all modules (0 deprecation warnings)
- FastAPI `@app.on_event("startup")` → `lifespan` context manager (deprecation fix)
- `pyproject.toml`: WeasyPrint constraint tightened to `>=68.1` (CVE-2025-68616 fix)
- `asyncio_mode = "auto"` added to pytest config

### Fixed
- 6 skipped tests resolved: Flask + pytest-httpx installed as dev dependencies
- `tests/test_failure_injection.py`: crypto stub guard prevents blocking real `cryptography.hazmat`
- `scripts/run_pipeline.py`: NameError (`args` outside `main()`) fixed
- `src/anchor/arbitrum_anchor.py`: created missing module (imported by 2 test files)
- `src/centinel/core/normalize.py`: `parse_obj()` → `model_validate()`, `class Config` → `ConfigDict`

### Security
- WeasyPrint pinned to `>=68.1` to exclude CVE-2025-68616 (SSRF via HTTP redirect)

---

## [0.1.0] — 2026-02-01

### Added
- Core pipeline: download → hash → normalize → analyze → anchor
- SHA-256 hash chain with Merkle root and OpenTimestamps anchoring
- 15 statistical detectors (Benford, participation, turnout, granularity, irreversibility, etc.)
- ML outlier detection via Isolation Forest (`ml_outliers_rule`)
- Multi-witness federation architecture
- FastAPI public API (`/snapshots`, `/hashchain/verify`, `/alerts`)
- Static-first CDN panel (GitHub Pages + Service Worker for offline mode)
- Emergency dispatch system with kill-switch and defensive mode
- Resilience: auto-resume with exponential backoff, chaos injection for testing
- Full CI/CD: GitHub Actions + CodeQL + Dependabot
- Security audit RT-01..RT-15 — all 15 issues closed, score 9.9/10
- 95 test files, 520 tests passing

### Architecture
- Python 3.10+, FastAPI, APScheduler, Poetry
- Zero proprietary dependencies (AGPL-3.0)
- Designed for Honduras general elections (18 departments, 96 JSON result files)

---

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for planned features.

- v0.3.0: Calibration with real HN-2025 data + UPNFM academic validation
- v0.4.0: Field pilot (1+ municipalities in live electoral event)
- v1.0.0: OTF grant milestone — validated in production electoral environment
