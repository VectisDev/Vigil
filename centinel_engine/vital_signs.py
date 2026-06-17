"""Re-export shim: centinel_engine.vital_signs → scripts.watchdog.

Shim de re-exportación: centinel_engine.vital_signs → scripts.watchdog.

The vital-signs adaptive resilience engine now lives in scripts/watchdog.py.
This shim preserves backward compatibility so existing callers continue to work.

ponytail: remove this shim once all callers import from scripts.watchdog directly.
Update: tests/test_vital_signs.py, tests/test_integration_loop.py,
tests/test_hostile_scenarios.py, and scripts/run_pipeline.py.
"""

from scripts.watchdog import (  # noqa: F401 — backward-compat re-exports
    DEFAULT_HEALTH_STATE,
    DEFAULT_THRESHOLDS,
    ResilienceMode,
    _compute_avg_latency,
    _compute_request_pressure,
    _compute_success_rate,
    _emit_alert,
    _policy_blocks_exceed_window,
    _resolve_threshold,
    check_vital_signs,
    load_health_state,
    load_vital_signs_config,
    predict_mode,
    save_health_state,
    update_status_after_scrape,
)
