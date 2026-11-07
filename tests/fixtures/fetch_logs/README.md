# Fetch-log fixtures

These files are pipeline state, not Honduras 2025 captures.

- `no_attempt.json` has no recorded request. Reachability must stay unknown.
- `consecutive_failures.json` records attempts that failed. Reachability may be false.

A gap between filenames in `tests/fixtures/hnd_2025/` is not one of these files. No fetch log was kept for that sample.
