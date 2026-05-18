# Centinel Engine — Claude Code Context

Electoral audit system for Honduras. Monitors CNE data in real time, chains snapshots cryptographically, runs 15 statistical detectors.

## Stack

- Python 3.10+, Poetry, FastAPI, APScheduler
- SHA-256 hash chain + Merkle + OpenTimestamps (Bitcoin anchoring)
- pytest (520 passing, 0 failing), GitHub Actions CI

## Key directories

```
src/centinel/          # Main package
  api/main.py          # FastAPI public API
  core/
    rules/             # 15 statistical detector modules + registry
    rules_engine.py    # Executes rules against snapshots
    normalize.py       # Pydantic V2 schema + CNE data normalization
  utils/config_loader.py

scripts/
  run_pipeline.py      # Main pipeline orchestrator (download→hash→analyze→anchor)
  generate_report.py   # Bilingual PDF report generator
  setup_wizard.py      # Interactive onboarding wizard
  validate_false_positive_rate.py  # FP validation (run: --iterations 500 --seed 42)
  calibrate_2025.py    # Batch calibration against real HN-2025 data

command_center/
  config.yaml          # Main config (edit CNE URL here)
  rules.yaml           # 15 rules with thresholds — single source of truth

src/anchor/
  arbitrum_anchor.py   # Ethereum/Arbitrum anchoring
  opentimestamps.py    # Bitcoin OTS anchoring

tests/                 # 520 passing tests
  integration/test_full_cycle.py
```

## Dev setup

```bash
poetry install
poetry run pytest tests/ --tb=short -q
```

## Run pipeline

```bash
make pipeline          # single run
make start             # background daemon
make wizard            # interactive setup
```

## Rules system

Rules live in `src/centinel/core/rules/*_rule.py`. Each uses `@rule(name=..., severity=..., config_key=...)` decorator from `registry.py`. Thresholds are in `command_center/rules.yaml` keyed by `config_key`.

To add a rule: create `src/centinel/core/rules/my_rule.py`, decorate function with `@rule(...)`, add config key to `rules.yaml`.

## Testing patterns

- `monkeypatch` for pipeline paths and external calls
- `pytest.importorskip("flask")` guards Flask-dependent tests
- Async tests use `asyncio_mode = "auto"` (no `@pytest.mark.asyncio` needed)
- Stubs for apscheduler, cryptography, dotenv in `test_failure_injection.py`

## Conventions

- Doc files: `UPPER-SNAKE-CASE.md`, bilingual (ES + EN), header `**Version:** X.Y | **Date:** YYYY-MM-DD | **Status:** Active`
- No `@app.on_event` — use FastAPI `lifespan` context manager
- Pydantic V2: `@field_validator`, `@model_validator`, `model_config = ConfigDict(...)`
- Commits: conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)
