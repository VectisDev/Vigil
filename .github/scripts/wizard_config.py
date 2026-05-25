#!/usr/bin/env python3
"""
Wizard step: write country + setup metadata to command_center/config.yaml.
Called by setup-wizard.yml with CENTINEL_COUNTRY env var set.
"""
import os, json
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
    _use_yaml = True
except ImportError:
    _use_yaml = False

COUNTRY = os.environ.get("CENTINEL_COUNTRY", "HN")
cfg_path = Path("command_center/config.yaml")

if _use_yaml and cfg_path.exists():
    cfg = yaml.safe_load(cfg_path.read_text()) or {}
else:
    cfg = {}

cfg.setdefault("centinel", {})
cfg["centinel"]["country"]      = COUNTRY
cfg["centinel"]["setup_at"]     = datetime.now(timezone.utc).isoformat()
cfg["centinel"]["setup_source"] = "github-actions-wizard"

cfg_path.parent.mkdir(parents=True, exist_ok=True)
if _use_yaml:
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
else:
    # Append country block at end of file if YAML not available
    existing = cfg_path.read_text() if cfg_path.exists() else ""
    if "centinel:" not in existing:
        cfg_path.write_text(existing + f"\ncentinel:\n  country: {COUNTRY}\n")

print(f"country={COUNTRY} written to {cfg_path}")
