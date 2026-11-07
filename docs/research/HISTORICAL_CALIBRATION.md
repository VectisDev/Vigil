# Historical calibration

The heuristic of 10 inconsistent actas per minute is **not** calibrated on another election.

## What was looked for

A second series of official presidential JSON, comparable to `tests/fixtures/hnd_2025/`, for Honduras 2013, 2017, or 2021.

## What is in this repository

Those directories are not here. There is no `tests/fixtures/hnd_2013`, `hnd_2017`, or `hnd_2021`. Comments in `command_center/rules.yaml` that say "calibrated" on Honduras 2025 were fit on the same 64 files they are then used to describe. That is exploratory.

## What this means

Do not cite 10 per minute as a capacity measured in the field, and do not cite it as a result that was locked before the 2025 files were inspected. The June 2026 hash in `docs/research/THRESHOLD_PREREGISTRATION.md` no longer matches the YAML.

If a later commit adds an independent series, the promotion gate in `tests/test_rule_promotion_gate.py` is how a rule leaves `promotion: exploratory`. Until that fixture exists, the negative result is this page.
