"""Orquesta reglas de análisis en tiempo real para snapshots del CNE.

English:
    Orchestrates real-time analysis rules for CNE snapshots.
"""

from __future__ import annotations

import glob
import json
import logging
import os
from datetime import datetime, timezone
from typing import Callable, List, Optional, Tuple

from scripts.download_and_hash import load_config
from sentinel.core.rules.benford_law_rule import apply as benford_apply
from sentinel.core.rules.basic_diff_rule import apply as diff_apply
from sentinel.core.rules.common import parse_timestamp
from sentinel.core.rules.irreversibility_rule import apply as irrevers_apply
from sentinel.core.rules.ml_outliers_rule import apply as outliers_apply
from sentinel.core.rules.participation_anomaly_rule import apply as participation_apply
from sentinel.core.rules.processing_speed_rule import apply as speed_apply
from sentinel.core.rules.trend_shift_rule import apply as trend_apply
from sentinel.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

RuleFn = Callable[[dict, Optional[dict], dict], List[dict]]

RULES: List[Tuple[str, RuleFn]] = [
    ("benford_law", benford_apply),
    ("ml_outliers", outliers_apply),
    ("basic_diff", diff_apply),
    ("participation_anomaly", participation_apply),
    ("trend_shift", trend_apply),
    ("processing_speed", speed_apply),
    ("irreversibility", irrevers_apply),
]


def load_json(file_path: str) -> Optional[dict]:
    """Carga un archivo JSON y registra fallos de lectura.

    Args:
        file_path: Ruta del archivo JSON.

    Returns:
        Diccionario cargado o None si falla.

    English:
        Loads a JSON file and logs read failures.

    Args:
        file_path: JSON file path.

    Returns:
        Loaded dictionary or None on failure.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001 - log and continue for robustness
        logger.error("load_error file_path=%s error=%s", file_path, e)
        return None


def run_all_rules(
    current_data: dict, previous_data: Optional[dict], full_config: dict
) -> List[dict]:
    """Ejecuta reglas habilitadas contra un snapshot actual.

    Args:
        current_data: Snapshot JSON actual del CNE.
        previous_data: Snapshot JSON anterior (None en el primer snapshot).
        full_config: Configuración completa cargada desde config.yaml.

    Returns:
        Lista consolidada de alertas en formato estándar.

    English:
        Runs enabled rules against a current snapshot.

    Args:
        current_data: Current CNE JSON snapshot.
        previous_data: Previous JSON snapshot (None for the first snapshot).
        full_config: Full configuration loaded from config.yaml.

    Returns:
        Consolidated list of alerts in the standard format.
    """
    rules_config = full_config.get("rules", {})
    if not rules_config.get("global_enabled", True):
        return []

    alerts: List[dict] = []
    for rule_name, rule_apply in RULES:
        rule_config = rules_config.get(rule_name, {})
        if not rule_config.get("enabled", True):
            continue
        try:
            alerts.extend(rule_apply(current_data, previous_data, rule_config))
        except Exception as exc:  # noqa: BLE001 - safety in rule execution
            logger.exception("rule_failed rule=%s error=%s", rule_name, exc)
    return alerts


def _enrich_alerts(alerts: List[dict], file_name: str, data: dict) -> List[dict]:
    timestamp = parse_timestamp(data)
    timestamp_str = timestamp.isoformat() if timestamp else None
    enriched = []
    for alert in alerts:
        payload = dict(alert)
        payload["snapshot"] = file_name
        if timestamp_str:
            payload["timestamp"] = timestamp_str
        enriched.append(payload)
    return enriched


def run_audit(target_directory: str = "data/normalized") -> None:
    """Ejecuta reglas sobre snapshots normalizados y genera reportes.

    Args:
        target_directory: Directorio con snapshots normalizados.

    English:
        Runs rules against normalized snapshots and generates reports.

    Args:
        target_directory: Directory containing normalized snapshots.
    """
    config = load_config()
    alerts_log: List[dict] = []

    file_list = sorted(glob.glob(os.path.join(target_directory, "*.json")))
    if not file_list:
        logger.warning("no_files_found target_directory=%s", target_directory)
        return

    logger.info(
        "processing_snapshots count=%s target_directory=%s",
        len(file_list),
        target_directory,
    )

    previous_data: Optional[dict] = None
    for file_path in file_list:
        data = load_json(file_path)
        if not data:
            continue
        file_name = os.path.basename(file_path)
        alerts = run_all_rules(data, previous_data, config)
        alerts_log.extend(_enrich_alerts(alerts, file_name, data))
        previous_data = data

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "alerts": alerts_log,
    }

    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
    with open("anomalies_report.json", "w", encoding="utf-8") as f:
        json.dump(alerts_log, f, indent=4, ensure_ascii=False)

    logger.info("audit_completed alerts=%s", len(alerts_log))


if __name__ == "__main__":
    run_audit()
