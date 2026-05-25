#!/usr/bin/env python3
"""
Wizard step: active endpoint discovery + schema detection.
Requires CENTINEL_COUNTRY env var. ELECTION_URL optional for non-HN countries.

Order of operations (must NOT be changed):
  1. Write ELECTION_URL to config/prod/endpoints.yaml["cne"]["main_url"] FIRST
  2. Instantiate ElectoralEndpointScanner (reads main_url from config)
  3. Run scanner → discovers real endpoints
  4. Write monitoring_mode + field_map + table_selector to both config files
  5. Do NOT call wizard_config.py here — the workflow does that separately
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    import yaml
    _use_yaml = True
except ImportError:
    print("ERROR: pyyaml required. Run: pip install pyyaml")
    sys.exit(1)

COUNTRY  = os.environ.get("CENTINEL_COUNTRY", "HN")
MAIN_URL = os.environ.get("ELECTION_URL", "").strip()

# ── Load preset ────────────────────────────────────────────────────────────
preset = None
try:
    from centinel.countries import LATAM_COUNTRIES
    preset = LATAM_COUNTRIES.get(COUNTRY)
    if preset:
        print(f"✓ Preset loaded: {preset.name} ({len(preset.divisions)} divisions)")
except Exception as e:
    print(f"WARNING: countries.py not available ({e})")

# For HN: derive base URL from preset national_url if not provided
if not MAIN_URL and preset and preset.national_url:
    MAIN_URL = preset.national_url.rsplit("/api/", 1)[0]
    print(f"ℹ️  HN: derived base URL from preset: {MAIN_URL}")

if not MAIN_URL:
    print(f"ERROR: ELECTION_URL env var required for {COUNTRY}")
    sys.exit(1)

# ── Step 1: Write main_url to endpoints.yaml BEFORE instantiating scanner ──
# The scanner reads main_url from config["cne"]["main_url"] in run()
ep_path = Path("config/prod/endpoints.yaml")
ep_cfg: dict = {}
if ep_path.exists():
    ep_cfg = yaml.safe_load(ep_path.read_text()) or {}
ep_cfg.setdefault("cne", {})
ep_cfg["cne"]["main_url"] = MAIN_URL
ep_path.parent.mkdir(parents=True, exist_ok=True)
ep_path.write_text(yaml.safe_dump(ep_cfg, sort_keys=False, allow_unicode=True))
print(f"✓ main_url written to {ep_path}: {MAIN_URL}")

# ── Step 2: Instantiate and run scanner ────────────────────────────────────
mode = getattr(preset, "monitoring_mode", "json") if preset else "json"
print(f"🔎 Scanning {COUNTRY} (mode={mode}) — {MAIN_URL}")

result = {"count": 0, "healthy_count": 0}
detected_field_map: dict = {}
table_result: dict | None = None

try:
    from centinel_engine.electoral_endpoint_scanner import ElectoralEndpointScanner

    scanner = ElectoralEndpointScanner(
        config_path=str(ep_path),
        country_preset=preset,
        timeout=15,
    )
    result = scanner.run()
    print(f"✓ Scanner: {result['count']} endpoints found, {result.get('healthy_count', 0)} healthy")

    # Auto-detect field_map from healthy endpoints
    if result["count"] > 0:
        # Re-fetch a sample payload to detect schema
        sample_payloads = []
        for ep_record in ep_cfg.get("cne", {}).get("presidential_endpoints", [])[:3]:
            url = ep_record.get("url") if isinstance(ep_record, dict) else getattr(ep_record, "url", None)
            if url:
                try:
                    import requests
                    r = requests.get(url, timeout=10)
                    r.raise_for_status()
                    sample_payloads.append(r.json())
                except Exception:
                    pass
        if sample_payloads:
            detected_field_map = scanner.detect_schema(sample_payloads)
            if detected_field_map:
                print(f"✓ Schema detected: {list(detected_field_map.keys())}")

except ImportError as e:
    print(f"WARNING: ElectoralEndpointScanner not available ({e}) — skipping discovery")
except Exception as e:
    print(f"WARNING: Scanner failed ({e}) — continuing without discovery")

# ── Step 3: Fallback to html_table if no JSON found ───────────────────────
if result["count"] == 0 and mode == "json":
    print("⚠  No JSON endpoints found — trying html_table mode via Playwright")
    try:
        from centinel_engine.electoral_endpoint_scanner import ElectoralEndpointScanner
        scanner = ElectoralEndpointScanner(config_path=str(ep_path), country_preset=preset, timeout=15)
        table_result = scanner.detect_html_table(MAIN_URL)
        if table_result:
            mode = "html_table"
            print(f"✓ HTML table detected — 24 rules will apply via table extraction")
        else:
            mode = "testimony"
            print(f"⚠  No structured data found — activating testimony mode")
    except Exception as e:
        mode = "testimony"
        print(f"⚠  html_table detection failed ({e}) — activating testimony mode")

# ── Step 4: Write monitoring_mode + field_map + table_selector ────────────
ep_cfg = yaml.safe_load(ep_path.read_text()) or {}
ep_cfg.setdefault("cne", {})
ep_cfg["cne"]["monitoring_mode"] = mode
if detected_field_map:
    ep_cfg["cne"]["field_map"] = detected_field_map
if table_result:
    ep_cfg["cne"]["table_selector"] = table_result.get("table_selector", "table")
    ep_cfg["cne"]["column_map"] = table_result.get("column_map", {})
ep_path.write_text(yaml.safe_dump(ep_cfg, sort_keys=False, allow_unicode=True))
print(f"✓ endpoints.yaml updated — mode={mode}")

# Same in command_center/config.yaml
cc_path = Path("command_center/config.yaml")
cc_cfg: dict = {}
if cc_path.exists():
    cc_cfg = yaml.safe_load(cc_path.read_text()) or {}
cc_cfg.setdefault("centinel", {})["monitoring_mode"] = mode
if detected_field_map:
    cc_cfg["field_map"] = detected_field_map
cc_path.parent.mkdir(parents=True, exist_ok=True)
cc_path.write_text(yaml.safe_dump(cc_cfg, sort_keys=False, allow_unicode=True))
print(f"✓ config.yaml updated — mode={mode}")

print(f"✓ Discovery complete: {result['count']} endpoints | {result.get('healthy_count', 0)} healthy | mode={mode}")
