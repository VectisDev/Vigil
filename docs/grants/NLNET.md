# NLnet — task note

This is not a second budget. The only funding total in the repository is **75,000 USD over 12 months**, in `BUDGET_NARRATIVE.md`, written for an OTF-shaped ask. This page does not add another amount.

## Task

A stranger can check a saved public JSON sample without trusting the operator and without installing the application.

## Acceptance tests already in the tree

| Check | Command | Pass |
|---|---|---|
| Raw files are not a hash chain | `make replay-offline` | exit of `verify_chain.py` is 1, status `orphans`, count 63 |
| Merkle root matches the committed root | same command | root `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780` |
| Same check inside a pinned image | `docker build -f Dockerfile.demo -t vigil-demo . && docker run --rm vigil-demo` | same outcomes |
| No fetch is not an outage | `tests/test_export_static_snapshot.py` | `reachable` is null |
| Critical rules are marked exploratory until an outside fixture exists | `tests/test_rule_promotion_gate.py` | no silent promotion |
| The 10/min figure is not calibrated on another election | `docs/research/HISTORICAL_CALIBRATION.md` | the earlier series are not in the repo |

## License

AGPL-3.0-only. Source: https://github.com/VectisDev/Vigil

## What this page does not claim

No partner institution, no filed NLnet application, no conference tour, and no finding about a party or a candidate. The 2025 numbers are the ones in `docs/evidence/HN2025.md`.
