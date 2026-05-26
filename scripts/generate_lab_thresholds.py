"""Generate web/lab-thresholds.json from real CENTINEL config files.

Run: python scripts/generate_lab_thresholds.py
Output: web/lab-thresholds.json

This script is read-only with respect to all operational configs.
It never writes to command_center/, config/prod/, or centinel_engine/.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent

SOURCE_FILES = [
    "command_center/config.yaml",
    "command_center/advanced_security_config.yaml",
    "command_center/attack_config.yaml",
    "config/prod/rate_limiter.yaml",
]


def _load(path: str) -> dict:
    full = ROOT / path
    if not full.exists():
        print(f"WARNING: {path} not found, using empty dict", file=sys.stderr)
        return {}
    with open(full, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _resolve(val, combined: dict):
    if callable(val):
        return val(combined)
    return val


def main() -> None:
    cfg_main = _load("command_center/config.yaml")
    cfg_adv = _load("command_center/advanced_security_config.yaml")
    cfg_atk = _load("command_center/attack_config.yaml")
    cfg_rl = _load("config/prod/rate_limiter.yaml")

    zt = cfg_main.get("security", {}).get("zero_trust_config", {})

    combined = {
        # from config.yaml > security > zero_trust
        "rate_limit_rpm": zt.get("rate_limit_rpm", 20),
        "max_body_bytes": zt.get("max_body_bytes", 1048576),
        # from config.yaml top-level
        "timestamp_max_age_hours": cfg_main.get("timestamp_max_age_hours", 2),
        "capture_interval_minutes": cfg_main.get("capture_interval_minutes", 30),
        # from advanced_security_config.yaml
        "honeypot_flood_trigger_count": cfg_adv.get("honeypot_flood_trigger_count", 2),
        "honeypot_flood_window_seconds": cfg_adv.get("honeypot_flood_window_seconds", 60),
        "honeypot_threshold_per_minute": cfg_adv.get("honeypot_threshold_per_minute", 100),
        "cpu_threshold_percent": cfg_adv.get("cpu_threshold_percent", 75),
        "cpu_sustain_seconds": cfg_adv.get("cpu_sustain_seconds", 90),
        # from attack_config.yaml
        "max_requests_per_ip": cfg_atk.get("max_requests_per_ip", 20),
        # from rate_limiter.yaml
        "max_requests_per_hour": cfg_rl.get("max_requests_per_hour", 240),
        "burst": cfg_rl.get("capacity", cfg_rl.get("burst", 5)),
        # derived: HN has 19 endpoints (nacional + 18 departments)
        "endpoint_count": len(cfg_main.get("sources", [])) or 19,
    }

    THRESHOLDS: dict[str, dict] = {
        "B1": {
            # Lab slider: req/s (DDoS multi-IP), min=100, max=400000
            # 20 req/min per IP × 50 IPs = 1000 req/min ≈ 16667 req/s → detectAt
            # breachAt: rate limiter capacity exhausted at max_requests_per_hour × 1000 scale
            "detectAt": lambda c: round(c["rate_limit_rpm"] * 50 * 1000 / 60),
            "breachAt": lambda c: round(c["max_requests_per_hour"] * 1000),
            "sliderMax": lambda c: c["max_requests_per_hour"] * 2000,
            "realLabel": lambda c: f"{c['rate_limit_rpm']} req/min por IP · {c['max_requests_per_hour']} req/h total",
        },
        "B2": {
            # Lab slider: intentos/tick (1 tick ≈ 5 min snapshot), min=1, max=100
            # honeypot_flood_trigger_count=2 hits in 60s → over 5 min ≈ 10 hits → detectAt
            # breachAt: honeypot_threshold_per_minute=100 / 5
            "detectAt": lambda c: round(c["honeypot_flood_trigger_count"] * 5),
            "breachAt": lambda c: min(100, round(c["honeypot_threshold_per_minute"] / 5)),
            "sliderMax": 100,
            "realLabel": lambda c: f"{c['honeypot_flood_trigger_count']} hits en {c['honeypot_flood_window_seconds']}s",
        },
        "B3": {
            # SHA-256 binary check (pass/fail) — lab slider = % tampered actas
            "detectAt": 5,
            "breachAt": 100,
            "sliderMax": 100,
            "realLabel": "Verificación SHA-256 binaria (pass/fail)",
        },
        "B5": {
            # consensus_threshold = max(2, int(n*0.75)+1) with n=5 witnesses
            # 5 witnesses: threshold=4 → 2 compromised = detectable, 3 = breach
            "detectAt": 2,
            "breachAt": 3,
            "sliderMax": 5,
            "realLabel": "Consenso ≥75%+1 de witnesses (multi_witness.py)",
        },
        "B6": {
            # Lab slider: minutes of fake TTL, min=5, max=480
            # detectAt: > capture_interval_minutes (data becomes stale)
            # breachAt: > timestamp_max_age_hours × 60 (validity window exceeded)
            "detectAt": lambda c: c.get("capture_interval_minutes", 30),
            "breachAt": lambda c: c.get("timestamp_max_age_hours", 2) * 60,
            "sliderMax": lambda c: max(480, c.get("timestamp_max_age_hours", 2) * 60 * 2),
            "realLabel": lambda c: f"TTL real: {c.get('timestamp_max_age_hours', 2)}h de tolerancia",
        },
        "B7": {
            # Strict monotonic timestamp check — any regression = anomaly
            # Lab slider: minutes of time distortion
            "detectAt": 1,
            "breachAt": lambda c: c.get("capture_interval_minutes", 30) * 2,
            "sliderMax": lambda c: c.get("capture_interval_minutes", 30) * 8,
            "realLabel": "Timestamps monotónicos estrictos",
        },
        "B10": {
            # Lab slider: compromised modules (1-5)
            # cpu_threshold_percent=75 sustained cpu_sustain_seconds=90 → quarantine
            "detectAt": 2,
            "breachAt": 4,
            "sliderMax": 5,
            "realLabel": lambda c: f"CPU ≥{c['cpu_threshold_percent']}% por {c['cpu_sustain_seconds']}s → cuarentena",
        },
        "B11": {
            # Lab slider: forged headers (1-20)
            # detectAt: exceeds max_requests_per_ip; breachAt: max of both limits (capped to 20)
            "detectAt": lambda c: min(20, c.get("max_requests_per_ip", 20)),
            "breachAt": lambda c: min(20, max(c.get("max_requests_per_ip", 20), c.get("rate_limit_rpm", 20))),
            "sliderMax": 20,
            "realLabel": lambda c: f"{c['rate_limit_rpm']} req/min por IP · max body {c['max_body_bytes'] // 1024}KB",
        },
        "B12": {
            # Gossip epidemic fan-out=3, 100 peers — cascade speed in ticks
            "detectAt": 2,
            "breachAt": 7,
            "sliderMax": 20,
            "realLabel": "Gossip epidémico fan-out=3, 100 peers máx",
        },
    }

    out: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_files": SOURCE_FILES,
        "thresholds": {},
    }

    for event_id, spec in THRESHOLDS.items():
        entry: dict = {}
        for key in ("detectAt", "breachAt", "sliderMax", "realLabel"):
            val = spec.get(key)
            if val is None:
                continue
            resolved = _resolve(val, combined)
            entry[key] = resolved
        out["thresholds"][event_id] = entry

    dest = ROOT / "web" / "lab-thresholds.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Generated {dest.relative_to(ROOT)}")
    for eid, t in out["thresholds"].items():
        print(f"  {eid}: detectAt={t.get('detectAt')} breachAt={t.get('breachAt')} — {t.get('realLabel','')}")


if __name__ == "__main__":
    main()
