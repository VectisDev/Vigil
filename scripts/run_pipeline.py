"""
VIGIL — Pipeline Runner
===========================
Punto de entrada del pipeline de auditoria electoral.
Electoral audit pipeline entry point.

Functions:
  - resolve_poll_interval_seconds: Return polling interval from config
  - resolve_poll_jitter_factor:    Return jitter factor from config
  - safe_run_pipeline / run_pipeline: Resilient pipeline execution with
    checkpointing, auto-resume, and chaos-injection support for testing.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from centinel.anchor.opentimestamps_client import MultichainAnchor
from centinel.core.anchoring_payload import build_diff_summary, compute_anchor_root
from centinel.core.custody import run_startup_verification
from centinel.core.transparency import compute_merkle_root
from centinel.defense import logger as core_logger
from centinel.defense.advanced_security import load_manager
from centinel.defense.attack_logger import AttackForensicsLogbook, AttackLogConfig, HoneypotServer
from centinel.defense.security import DefensiveSecurityManager, SecurityConfig
from centinel.paths import iter_all_hashes, iter_all_snapshots
from centinel.utils.config_loader import load_config as load_pipeline_config
from centinel_engine import proxy_manager, secure_backup
import scripts.watchdog as vital_signs
from centinel_engine.config_loader import load_config as load_engine_config
from centinel_engine.rate_limiter import get_rate_limiter
from centinel_engine.secure_backup import BackupScheduler
from scripts.download_and_hash import is_master_switch_on, normalize_master_switch


logger = logging.getLogger("centinel.pipeline")

DATA_DIR = Path("data")
TEMP_DIR = DATA_DIR / "temp"
HASH_DIR = Path("hashes")
ANALYSIS_DIR = Path("analysis")
REPORTS_DIR = Path("reports")
ANCHOR_LOG_DIR = Path("logs") / "anchors"

# ponytail: Phase 1c — unified state.json with namespaced keys.
# Full unification pending test refactor of test_failure_injection.py (monkeypatches
# individual constants). For now STATE_UNIFIED_PATH is written atomically; individual
# constants are kept as deprecated aliases for external readers (watchdog.py, export_static_snapshot.py).
# When to complete: update _set_pipeline_paths in tests + remove individual path refs in watchdog.py.
STATE_UNIFIED_PATH = DATA_DIR / "state.json"
STATE_PATH = DATA_DIR / "pipeline_state.json"            # deprecated alias → state["pipeline"]
PIPELINE_CHECKPOINT_PATH = TEMP_DIR / "pipeline_checkpoint.json"  # deprecated alias → state["resilience"]
FAILURE_CHECKPOINT_PATH = TEMP_DIR / "checkpoint.json"   # deprecated alias → state["checkpoint"]
HEARTBEAT_PATH = DATA_DIR / "heartbeat.json"             # deprecated alias → state["heartbeat"]
SECURITY_CONFIG_PATH = Path("command_center") / "security_config.yaml"
ATTACK_CONFIG_PATH = Path("command_center") / "attack_config.yaml"
ADVANCED_SECURITY_CONFIG_PATH = Path("command_center") / "advanced_security_config.yaml"
RESILIENCE_STAGE_ORDER = [
    "start",
    "healthcheck",
    "download",
    "normalize",
    "analyze",
    "report",
    "anchor",
]


def _write_atomic(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically via a temp file + os.replace().

    Escribe JSON atómicamente usando archivo temporal + os.replace().
    Prevents torn reads during concurrent pipeline restarts.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def _read_unified(ns: str) -> dict[str, Any]:
    """Read one namespace from the unified state.json, falling back to empty dict.

    Lee un namespace del state.json unificado; retorna dict vacío si no existe.
    """
    if not STATE_UNIFIED_PATH.exists():
        return {}
    try:
        state = json.loads(STATE_UNIFIED_PATH.read_text(encoding="utf-8"))
        return state.get(ns, {}) if isinstance(state, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write_unified(ns: str, data: dict[str, Any]) -> None:
    """Write one namespace to the unified state.json atomically.

    Escribe un namespace en state.json unificado de forma atómica.
    """
    state: dict[str, Any] = {}
    if STATE_UNIFIED_PATH.exists():
        try:
            state = json.loads(STATE_UNIFIED_PATH.read_text(encoding="utf-8")) or {}
        except (json.JSONDecodeError, OSError):
            state = {}
    if not isinstance(state, dict):
        state = {}
    state[ns] = data
    _write_atomic(STATE_UNIFIED_PATH, state)


def log_event(log: logging.Logger, level: int, event: str, **kwargs: Any) -> None:
    """Structured log event. / Evento de log estructurado."""
    log.log(level, event, extra=kwargs)


def utcnow() -> datetime:
    """Get current UTC time. / Obtiene hora UTC actual."""
    return datetime.now(timezone.utc)


def update_heartbeat(status: str = "ok", details: dict[str, Any] | None = None) -> None:
    """Update heartbeat in unified state.json and legacy file for monitoring.

    Actualiza heartbeat en state.json unificado y archivo legacy para monitoreo.
    """
    payload = {
        "updated_at": utcnow().isoformat(),
        "status": status,
        "pid": os.getpid(),
    }
    if details:
        payload["details"] = details
    try:
        _write_unified("heartbeat", payload)
        # Keep legacy file for watchdog.py and external readers (backward compat)
        _write_atomic(HEARTBEAT_PATH, payload)
    except OSError as exc:
        logger.warning("heartbeat_write_failed path=%s error=%s", HEARTBEAT_PATH, exc)


def load_state() -> dict[str, Any]:
    """Load pipeline state from unified state.json (namespace 'pipeline').

    Carga estado del pipeline desde state.json unificado (namespace 'pipeline').
    """
    data = _read_unified("pipeline")
    if data:
        return data
    # Backward compat: fall back to legacy pipeline_state.json
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("pipeline_state_invalid path=%s error=%s", STATE_PATH, exc)
        return {}


def save_state(state: dict[str, Any]) -> None:
    """Save pipeline state atomically to unified state.json and legacy file.

    Guarda estado del pipeline atómicamente en state.json unificado y archivo legacy.
    """
    _write_unified("pipeline", state)
    _write_atomic(STATE_PATH, state)


def load_pipeline_checkpoint() -> dict[str, Any]:
    """Load pipeline checkpoint from unified state.json (namespace 'resilience').

    Carga checkpoint del pipeline desde state.json unificado (namespace 'resilience').
    """
    data = _read_unified("resilience")
    if data:
        return data
    if not PIPELINE_CHECKPOINT_PATH.exists():
        return {}
    try:
        return json.loads(PIPELINE_CHECKPOINT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("pipeline_checkpoint_invalid path=%s error=%s", PIPELINE_CHECKPOINT_PATH, exc)
        return {}


def save_pipeline_checkpoint(payload: dict[str, Any]) -> None:
    """Persist pipeline checkpoint atomically to unified state.json and legacy file.

    Guarda checkpoint del pipeline atómicamente en state.json unificado y archivo legacy.
    """
    _write_unified("resilience", payload)
    _write_atomic(PIPELINE_CHECKPOINT_PATH, payload)


def clear_pipeline_checkpoint() -> None:
    """Clear pipeline checkpoint from unified state and legacy file.

    Elimina checkpoint del pipeline del estado unificado y archivo legacy.
    """
    _write_unified("resilience", {})
    if PIPELINE_CHECKPOINT_PATH.exists():
        PIPELINE_CHECKPOINT_PATH.unlink()


def load_resilience_checkpoint() -> dict[str, Any]:
    """Load resilience checkpoint from unified state.json (namespace 'checkpoint').

    Carga checkpoint de resiliencia desde state.json unificado (namespace 'checkpoint').
    """
    data = _read_unified("checkpoint")
    if data:
        return data if isinstance(data, dict) else {}
    if not FAILURE_CHECKPOINT_PATH.exists():
        return {}
    try:
        payload = json.loads(FAILURE_CHECKPOINT_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        logger.warning("resilience_checkpoint_invalid path=%s", FAILURE_CHECKPOINT_PATH)
        return {}


def collect_snapshot_index(limit: int = 19) -> list[dict[str, Any]]:
    """Generate a JSON index with recent snapshots. / Genera indice JSON con snapshots recientes."""
    all_snapshots = iter_all_snapshots(data_root=DATA_DIR)
    snapshots = sorted(all_snapshots, key=lambda p: p.stat().st_mtime, reverse=True)
    index: list[dict[str, Any]] = []
    for snapshot in snapshots[:limit]:
        index.append(
            {
                "file": str(snapshot.relative_to(DATA_DIR)),
                "mtime": snapshot.stat().st_mtime,
            }
        )
    return index


def build_defensive_state_snapshot() -> dict[str, Any]:
    """Build persisted state for defensive shutdown.

    Construye estado persistible para shutdown defensivo.
    """
    all_snaps = iter_all_snapshots(data_root=DATA_DIR)
    latest_snapshot = all_snaps[-1] if all_snaps else None
    all_hashes = iter_all_hashes(hash_root=HASH_DIR)
    recent_hashes = [str(p.relative_to(HASH_DIR)) for p in reversed(all_hashes[-10:])]
    queued_urls: list[str] = []
    config = load_pipeline_config()
    endpoints = config.get("endpoints") if isinstance(config, dict) else None
    if isinstance(endpoints, dict):
        queued_urls = [str(url) for url in endpoints.values()][:25]
    return {
        "latest_snapshot": latest_snapshot.name if latest_snapshot else None,
        "recent_hash_files": recent_hashes,
        "queued_urls": queued_urls,
        "recent_snapshots": collect_snapshot_index(limit=10),
        "checkpoint": load_pipeline_checkpoint(),
        "heartbeat": json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8")) if HEARTBEAT_PATH.exists() else {},
    }


def load_rules_thresholds() -> dict[str, Any]:
    """Load rules from config/prod/rules.yaml. / Carga reglas desde config/prod/rules.yaml."""
    try:
        payload = load_engine_config("rules.yaml", env="prod")
        return payload if isinstance(payload, dict) else {}
    except ValueError as exc:
        logger.warning("rules_yaml_invalid error=%s", exc)
        return {}


def load_security_settings() -> dict[str, Any]:
    """Load security settings from rules.yaml.

    Carga configuracion de seguridad desde rules.yaml.
    """
    rules_thresholds = load_rules_thresholds()
    security = rules_thresholds.get("security", {}) if isinstance(rules_thresholds, dict) else {}
    return security if isinstance(security, dict) else {}


def load_resilience_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Load resilience settings from main config.

    Carga configuracion de resiliencia desde el config principal.
    """
    resilience = config.get("resilience", {}) if isinstance(config, dict) else {}
    return resilience if isinstance(resilience, dict) else {}


def load_circuit_breaker_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Load circuit breaker settings. / Carga configuracion de circuit breaker."""
    breaker = config.get("circuit_breaker", {}) if isinstance(config, dict) else {}
    return breaker if isinstance(breaker, dict) else {}


def load_low_profile_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Load low-profile settings. / Carga configuracion low-profile."""
    low_profile = config.get("low_profile", {}) if isinstance(config, dict) else {}
    return low_profile if isinstance(low_profile, dict) else {}


def resolve_alert_paths(config: dict[str, Any]) -> tuple[Path, Path]:
    """Resolve paths for critical alerts. / Resuelve rutas para alertas criticas."""
    alerts_config = config.get("alerts", {}) if isinstance(config, dict) else {}
    if not isinstance(alerts_config, dict):
        alerts_config = {}
    alerts_log_path = Path(alerts_config.get("log_path", "alerts.log"))
    alerts_output_path = Path(alerts_config.get("output_path", "data/alerts.json"))
    return alerts_log_path, alerts_output_path


def build_chaos_rng(resilience: dict[str, Any]) -> random.Random:
    """Build random generator for chaos. / Construye generador aleatorio para caos."""
    chaos_settings = resilience.get("chaos", {}) if isinstance(resilience, dict) else {}
    if not isinstance(chaos_settings, dict):
        return random.Random()
    seed = chaos_settings.get("seed")
    return random.Random(seed)


def maybe_inject_chaos_failure(stage: str, resilience: dict[str, Any], rng: random.Random) -> None:
    """Inject chaos failure when enabled. / Inyecta falla caotica si esta habilitado."""
    chaos_settings = resilience.get("chaos", {}) if isinstance(resilience, dict) else {}
    if not isinstance(chaos_settings, dict):
        return
    if not chaos_settings.get("enabled", False):
        return
    failure_rate = float(chaos_settings.get("failure_rate", 0.0))
    if failure_rate <= 0:
        return
    if rng.random() < min(max(failure_rate, 0.0), 1.0):
        raise RuntimeError(f"chaos_injected stage={stage}")


def build_auto_resume_settings(resilience: dict[str, Any]) -> dict[str, Any]:
    """Normalize auto-resume settings. / Normaliza configuracion de auto-resume."""
    auto_resume = resilience.get("auto_resume", {}) if isinstance(resilience, dict) else {}
    if not isinstance(auto_resume, dict):
        auto_resume = {}
    return {
        "enabled": bool(auto_resume.get("enabled", True)),
        "max_attempts": int(auto_resume.get("max_attempts", 3)),
        "backoff_base_seconds": float(auto_resume.get("backoff_base_seconds", 5)),
        "backoff_max_seconds": float(auto_resume.get("backoff_max_seconds", 60)),
        "retry_on": str(auto_resume.get("retry_on", "any")).lower(),
    }


def compute_backoff_delay(attempt: int, base_seconds: float, max_seconds: float) -> float:
    """Compute exponential backoff delay. / Calcula backoff exponencial."""
    if attempt <= 0:
        return 0.0
    delay = base_seconds * (2 ** (attempt - 1))
    return min(max(delay, 0.0), max_seconds)


def resolve_max_json_limit(config: dict[str, Any]) -> int:
    """Resolve presidential JSON limit. / Resuelve limite de JSON presidenciales."""
    rules_thresholds = load_rules_thresholds()
    return int(rules_thresholds.get("max_json_presidenciales", config.get("max_sources_per_cycle", 19)))


def build_snapshot_queue(limit: int) -> list[Path]:
    """Build ordered snapshot list. / Construye lista ordenada de snapshots."""
    snapshots = iter_all_snapshots(data_root=DATA_DIR)
    return snapshots[-limit:]


def run_command(command: list[str], description: str, env: dict[str, str] | None = None) -> None:
    """Execute a system command. / Ejecuta un comando del sistema."""
    if not command:
        raise ValueError("Command list cannot be empty.")
    executable = shutil.which(command[0])
    if not executable:
        raise FileNotFoundError(f"Command not found: {command[0]}")
    full_command = [executable, *command[1:]]
    print(f"[+] {description}: {' '.join(full_command)}")
    subprocess.run(full_command, check=True, env=env)  # nosec B603


def latest_file(directory: Path, pattern: str) -> Path | None:
    """Get newest file by pattern. / Obtiene archivo mas reciente por patron."""
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def compute_content_hash(snapshot_path: Path) -> str:
    """Compute snapshot content hash. / Calcula hash de contenido del snapshot."""
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    normalized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def should_normalize(snapshot_path: Path) -> bool:
    """Determine if normalization is required. / Determina si requiere normalizacion."""
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    return "resultados" in payload and "estadisticas" in payload


def build_alerts(anomalies: list[dict[str, Any]], *, severity: str = "HIGH") -> list[dict[str, Any]]:
    """Build alerts from anomalies. / Construye alertas desde anomalias."""
    if not anomalies:
        return []

    files = [a.get("file") for a in anomalies if a.get("file")]
    from_file = min(files) if files else "unknown"
    to_file = max(files) if files else "unknown"
    alerts = []
    for anomaly in anomalies:
        rule = anomaly.get("type", "ANOMALY")
        description = anomaly.get("description") or anomaly.get("descripcion")
        alert = {"rule": rule, "severity": severity}
        if description:
            alert["description"] = description
        alerts.append(alert)

    return [
        {
            "from": from_file,
            "to": to_file,
            "alerts": alerts,
        }
    ]


def emit_critical_alerts(
    critical_anomalies: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    run_id: str,
) -> None:
    """Emit critical alerts to JSON and log. / Emite alertas criticas en JSON y log."""
    if not critical_anomalies:
        return
    alerts_payload = build_alerts(critical_anomalies, severity="CRITICAL")
    alerts_log_path, alerts_output_path = resolve_alert_paths(config)
    alerts_output_path.parent.mkdir(parents=True, exist_ok=True)
    alerts_output_path.write_text(json.dumps(alerts_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    alerts_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_lines = [
        json.dumps(
            {
                "timestamp": utcnow().isoformat(),
                "run_id": run_id,
                "severity": "CRITICAL",
                "rule": alert.get("rule"),
                "description": alert.get("description", ""),
            },
            ensure_ascii=False,
        )
        for window in alerts_payload
        for alert in window.get("alerts", [])
    ]
    if log_lines:
        with alerts_log_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(log_lines) + "\n")
    log_event(
        logger,
        logging.CRITICAL,
        "critical_alerts_detected",
        run_id=run_id,
        count=len(critical_anomalies),
    )


def critical_rules(config: dict[str, Any]) -> set[str]:
    """Resolve critical rules from configuration. / Resuelve reglas criticas desde configuracion."""
    raw_rules = config.get("alerts", {}).get("critical_anomaly_types", [])
    if isinstance(raw_rules, str):
        raw_list = [rule.strip() for rule in raw_rules.split(",") if rule.strip()]
    else:
        raw_list = [str(rule).strip() for rule in raw_rules if str(rule).strip()]
    return {rule.upper() for rule in raw_list}


def filter_critical_anomalies(anomalies: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Filter critical anomalies by rules. / Filtra anomalias criticas segun reglas."""
    rules = critical_rules(config)
    if not rules:
        return anomalies
    return [anomaly for anomaly in anomalies if anomaly.get("type", "").upper() in rules]


def should_generate_report(state: dict[str, Any], now: datetime) -> bool:
    """Determine if report cadence allows generation. / Determina si generar reporte por cadencia."""
    last_report = state.get("last_report_at")
    if not last_report:
        return True
    last_dt = datetime.fromisoformat(last_report)
    elapsed = now - last_dt
    return elapsed >= timedelta(hours=1)


def update_daily_summary(state: dict[str, Any], now: datetime, anomalies_count: int) -> None:
    """Update daily summary. / Actualiza resumen diario."""
    today = now.date().isoformat()
    daily = state.get("daily_summary", {})
    if daily.get("date") != today:
        if daily:
            summary_path = REPORTS_DIR / f"daily_summary_{daily['date']}.txt"
            summary_lines = [
                f"Resumen diario {daily['date']} UTC",
                f"Ejecuciones: {daily.get('runs', 0)}",
                f"Anomalias detectadas: {daily.get('anomalies', 0)}",
            ]
            summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

        daily = {"date": today, "runs": 0, "anomalies": 0}

    daily["runs"] += 1
    daily["anomalies"] += anomalies_count
    state["daily_summary"] = daily


def perform_cne_preflight_request(
    config: dict[str, Any],
    proxy: dict[str, str] | None,
    user_agent: str,
    timeout: float = 10.0,
    request_headers: dict[str, str] | None = None,
) -> int:
    """Perform the preflight CNE request with proxy and User-Agent integration.

    Bilingual: Ejecuta el request preflight al CNE con integracion de proxy
    y User-Agent.

    Args:
        config: Pipeline configuration dictionary.
        proxy: Proxy dictionary for ``requests`` or ``None`` for direct mode.
        user_agent: User-Agent string selected by proxy manager.
        timeout: Timeout in seconds for the preflight request.
        request_headers: Optional pre-built header mapping for anti-fingerprinting.

    Returns:
        HTTP status code from the preflight request.

    Raises:
        ValueError: If no endpoint can be resolved from config.
        requests.RequestException: If the HTTP request fails.
    """
    endpoints = config.get("endpoints", {}) if isinstance(config, dict) else {}
    if not isinstance(endpoints, dict):
        endpoints = {}
    preflight_url = (
        config.get("healthcheck_url")
        or config.get("base_url")
        or endpoints.get("nacional")
        or endpoints.get("fallback_nacional")
    )
    if not preflight_url:
        raise ValueError("Missing preflight URL for CNE connectivity check")

    headers: dict[str, str] = dict(request_headers or {"User-Agent": user_agent})
    response = requests.head(
        str(preflight_url),
        timeout=timeout,
        allow_redirects=True,
        headers=headers,
        proxies=proxy,
    )
    return int(response.status_code)


def process_snapshot_queue(
    snapshots: list[Path],
    checkpoint: dict[str, Any],
    *,
    run_id: str,
) -> tuple[list[str], int, Path | None]:
    """Process snapshots with advanced checkpointing.

    Procesa snapshots con checkpointing avanzado.
    """
    processed_hashes = list(checkpoint.get("processed_hashes", []))
    start_index = int(checkpoint.get("current_index", 0))
    snapshot_index = collect_snapshot_index(limit=len(snapshots))
    latest_snapshot: Path | None = snapshots[-1] if snapshots else None

    for idx in range(start_index, len(snapshots)):
        snapshot_path = snapshots[idx]
        try:
            content_hash = compute_content_hash(snapshot_path)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "snapshot_hash_failed path=%s error=%s",
                snapshot_path,
                exc,
            )
            continue
        processed_hashes.append(content_hash)
        save_resilience_checkpoint(
            run_id,
            "checkpoint",
            latest_snapshot=snapshot_path,
            content_hash=content_hash,
            processed_hashes=processed_hashes,
            snapshot_index=snapshot_index,
            current_index=idx + 1,
        )

    return processed_hashes, start_index, latest_snapshot


def save_resilience_checkpoint(
    run_id: str,
    stage: str | None,
    *,
    latest_snapshot: Path | None = None,
    content_hash: str | None = None,
    error: str | None = None,
    processed_hashes: list[str] | None = None,
    snapshot_index: list[dict[str, Any]] | None = None,
    current_index: int | None = None,
) -> None:
    """Persist intermediate state with hashes and JSON index.

    Guarda estado intermedio con hashes e indice JSON.
    """
    existing = load_resilience_checkpoint()
    payload = {
        **existing,
        "run_id": run_id,
        "stage": stage or "unknown",
        "timestamp": utcnow().isoformat(),
        "hashes": collect_recent_hashes(),
        "snapshot_index": snapshot_index or collect_snapshot_index(),
        "latest_snapshot": (
            str(latest_snapshot.relative_to(DATA_DIR))
            if latest_snapshot and DATA_DIR in latest_snapshot.parents
            else latest_snapshot.name if latest_snapshot else existing.get("latest_snapshot")
        ),
        "last_content_hash": content_hash or existing.get("last_content_hash"),
    }
    if error:
        payload["error"] = error
    if processed_hashes is not None:
        payload["processed_hashes"] = processed_hashes
    if current_index is not None:
        payload["current_index"] = current_index
    _write_unified("checkpoint", payload)
    _write_atomic(FAILURE_CHECKPOINT_PATH, payload)


def collect_recent_hashes(limit: int = 19) -> list[dict[str, Any]]:
    """Collect recent hashes for checkpoint. / Recolecta hashes recientes para checkpoint."""
    all_h = iter_all_hashes(hash_root=HASH_DIR)
    hash_files = list(reversed(all_h))[:limit]
    hashes: list[dict[str, Any]] = []
    for hash_file in hash_files:
        try:
            payload = json.loads(hash_file.read_text(encoding="utf-8"))
            hashes.append(
                {
                    "file": hash_file.name,
                    "hash": payload.get("hash"),
                    "chained_hash": payload.get("chained_hash"),
                }
            )
        except json.JSONDecodeError:
            logger.warning("checkpoint_hash_invalid path=%s", hash_file)
    return hashes


def clear_resilience_checkpoint() -> None:
    """Clear resilience checkpoint from unified state and legacy file.

    Elimina checkpoint de resiliencia del estado unificado y archivo legacy.
    """
    _write_unified("checkpoint", {})
    if FAILURE_CHECKPOINT_PATH.exists():
        FAILURE_CHECKPOINT_PATH.unlink()


def should_run_stage(current_stage: str, start_stage: str) -> bool:
    """Determine if a stage should run when resuming.

    Determina si una etapa debe ejecutarse al reanudar.
    """
    try:
        return RESILIENCE_STAGE_ORDER.index(current_stage) >= RESILIENCE_STAGE_ORDER.index(start_stage)
    except ValueError:
        return True


def resolve_poll_interval_seconds(config: dict[str, Any]) -> float:
    """Return configured polling interval in seconds.

    ES: Retorna el intervalo de polling configurado en segundos.
    Priority: low_profile.base_interval_minutes > poll_interval_seconds >
    election_interval_seconds > poll_interval_minutes > 180s default.

    Args:
        config: Pipeline configuration dictionary.

    Returns:
        Polling interval in seconds (float, always >= 30).
    """
    # Low-profile mode overrides: use base_interval_minutes if present
    low_profile = config.get("low_profile", {})
    if isinstance(low_profile, dict) and low_profile.get("enabled", False):
        base_min = low_profile.get("base_interval_minutes")
        if base_min is not None:
            try:
                return max(30.0, float(base_min) * 60.0)
            except (TypeError, ValueError):
                pass

    for key, multiplier in (
        ("poll_interval_seconds", 1.0),
        ("election_interval_seconds", 1.0),
        ("interval_seconds", 1.0),
        ("poll_interval_minutes", 60.0),
    ):
        val = config.get(key)
        if val is not None:
            try:
                return max(30.0, float(val) * multiplier)
            except (TypeError, ValueError):
                pass
    return 180.0  # default: 3 minutes


def resolve_poll_jitter_factor(
    config: dict[str, Any],
    rng: "Any | None" = None,
) -> float:
    """Return a jitter multiplier for the polling interval.

    ES: Retorna un multiplicador de jitter para el intervalo de polling.
    Returns a value in [1-jitter, 1+jitter] when rng is provided,
    or the raw jitter fraction when rng is None.

    Args:
        config: Pipeline configuration dictionary.
        rng:    Optional random.Random instance. When provided, returns a
                sampled multiplier in [1-p, 1+p]. When None, returns the
                raw fraction clamped to [0.0, 0.5].

    Returns:
        Float jitter value.
    """
    import random as _random

    low_profile = config.get("low_profile", {})
    if isinstance(low_profile, dict) and low_profile.get("enabled", False):
        jitter_pct = low_profile.get("jitter_percent", 10)
        try:
            fraction = max(0.0, min(50.0, float(jitter_pct))) / 100.0
        except (TypeError, ValueError):
            fraction = 0.1
    else:
        try:
            fraction = max(0.0, min(0.5, float(config.get("poll_jitter_factor", 0.1))))
        except (TypeError, ValueError):
            fraction = 0.1

    if rng is not None:
        # Return sampled multiplier: uniform in [1-fraction, 1+fraction]
        _rng = rng if hasattr(rng, "uniform") else _random.Random()
        return _rng.uniform(1.0 - fraction, 1.0 + fraction)

    return fraction


def _trigger_emergency_publish(reason: str = "anomaly_detected") -> None:
    """Call GitHub workflow_dispatch to push snapshot.json immediately on HIGH/CRITICAL anomaly.

    Requires GITHUB_TOKEN and GITHUB_REPOSITORY env vars.
    Fails silently — local chain and hash chain are the primary record.
    """
    import urllib.request as _urllib_req

    token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if not token or not repo:
        log_event(logger, logging.DEBUG, "emergency_publish_skipped_no_token")
        return

    payload = json.dumps({"ref": branch, "inputs": {"reason": reason}}).encode()
    req = _urllib_req.Request(
        f"https://api.github.com/repos/{repo}/actions/workflows/emergency-publish.yml/dispatches",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    try:
        with _urllib_req.urlopen(req, timeout=10) as resp:  # nosec B310
            log_event(logger, logging.INFO, "emergency_publish_triggered", status=resp.status, reason=reason)
    except Exception as exc:
        log_event(logger, logging.WARNING, "emergency_publish_failed", error=str(exc))


def _publish_forensics(config: dict[str, Any], now: datetime, extra_meta: dict | None = None) -> None:
    """/** Publica forenses + cobertura al panel público. / Publish forensics + coverage to public panel. **

    Always non-fatal: local SQLite + hash chain remain the source of truth.
    Siempre no fatal: SQLite local + cadena de hashes son la fuente de verdad.
    """
    try:
        from centinel.sync import forensics_publisher

        snapshots = iter_all_snapshots(data_root=DATA_DIR)
        if not snapshots:
            return

        hash_files = iter_all_hashes(hash_root=HASH_DIR)
        leaf_hashes = [p.read_text(encoding="utf-8").strip() for p in hash_files if p.exists()]
        leaf_hashes = [h for h in leaf_hashes if h]
        chain_hash = leaf_hashes[-1] if leaf_hashes else ""
        merkle_root = compute_merkle_root(leaf_hashes) or chain_hash or ""

        cadence_minutes = max(resolve_poll_interval_seconds(config) / 60.0, 1.0)

        forensics_publisher.run_and_publish(
            snapshots,
            captured_at=now.isoformat(),
            chain_hash=chain_hash,
            merkle_root=merkle_root,
            chain_length=len(leaf_hashes),
            target_cadence_minutes=cadence_minutes,
            endpoints_yaml_path=Path("config/prod/endpoints.yaml"),
            extra_meta=extra_meta,
        )
    except Exception as exc:  # noqa: BLE001 - publishing must never break pipeline
        log_event(logger, logging.WARNING, "forensics_publish_failed", error=str(exc))


def _anchor_snapshot(
    config: dict[str, Any],
    state: dict[str, Any],
    now: datetime,
    snapshot_path: Path,
) -> None:
    """/** Genera hash raíz post-reglas y ancla snapshot vía OpenTimestamps. / Generate post-rule root hash and anchor snapshot via OpenTimestamps. **"""
    current_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshots = iter_all_snapshots(data_root=DATA_DIR)
    previous_snapshot = snapshots[-2] if len(snapshots) > 1 else None
    previous_payload = json.loads(previous_snapshot.read_text(encoding="utf-8")) if previous_snapshot else None

    diff_summary = build_diff_summary(previous_payload, current_payload)

    rules_report_path = ANALYSIS_DIR / f"rules_report_{snapshot_path.stem}.json"
    rules_payload: dict[str, Any] = {}
    if rules_report_path.exists():
        report = json.loads(rules_report_path.read_text(encoding="utf-8"))
        rules_payload = {
            "alerts": report.get("alerts", []),
            "critical_alerts": report.get("critical_alerts", []),
            "pause_snapshots": report.get("pause_snapshots", []),
        }

    anchor_hashes = compute_anchor_root(current_payload, diff_summary, rules_payload)
    root_hash = anchor_hashes["root_hash"]

    # Submit root hash to Bitcoin via OpenTimestamps (Zero Cost anchoring)
    anchor = MultichainAnchor()
    checkpoint = anchor.anchor_checkpoint({"timestamp": now.isoformat(), "merkle_root": root_hash})
    if checkpoint.get("anchor_chain") == "bitcoin":
        ots_dir = ANCHOR_LOG_DIR / "ots"
        ots_dir.mkdir(parents=True, exist_ok=True)
        ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ots_path = ots_dir / f"{ts_slug}_{root_hash[:12]}.ots"
        ots_path.write_text(str(checkpoint.get("ots_proof", "")), encoding="utf-8")
        proof_meta = ots_dir / f"{ts_slug}_{root_hash[:12]}.json"
        proof_meta.write_text(json.dumps(checkpoint, indent=2, default=str), encoding="utf-8")
        logger.info(
            "ots_proof_saved path=%s bitcoin_tx=%s",
            ots_path,
            checkpoint.get("bitcoin_tx", "pending"),
        )
    else:
        logger.warning("ots_proof_unavailable root_hash=%s", root_hash[:16])


def _has_private_key(arbitrum_config: dict[str, Any]) -> bool:
    """Determine if a private key is available.

    Determina si hay private key disponible.

    Note: Arbitrum anchoring was removed (Zero Cost); retained only so
    ``_anchor_if_due`` can short-circuit cleanly when ``arbitrum.enabled``
    is left in legacy configs.
    """
    raw_key = arbitrum_config.get("private_key")
    placeholder_values = {"", None, "0x...", "REPLACE_ME"}
    if raw_key not in placeholder_values:
        return True
    return bool(os.getenv("ARBITRUM_PRIVATE_KEY"))


def _read_hashes_for_anchor(batch_size: int) -> list[str]:
    """Read recent hashes for anchoring. / Lee hashes recientes para anclaje."""
    all_h = iter_all_hashes(hash_root=HASH_DIR)
    hash_files_desc = list(reversed(all_h))
    selected = list(reversed(hash_files_desc[:batch_size]))
    hashes: list[str] = []
    for hash_file in selected:
        try:
            payload = json.loads(hash_file.read_text(encoding="utf-8"))
            hash_value = payload.get("hash") or payload.get("chained_hash")
            if hash_value:
                hashes.append(hash_value)
        except json.JSONDecodeError:
            logger.warning("hash_file_invalid path=%s", hash_file)
    return hashes


def _should_anchor(state: dict[str, Any], now: datetime, interval_minutes: int) -> bool:
    """Determine whether to anchor based on interval.

    Determina si debe anclarse segun intervalo.
    """
    last_anchor = state.get("last_anchor_at")
    if not last_anchor:
        return True
    try:
        last_dt = datetime.fromisoformat(last_anchor)
    except ValueError:
        return True
    return now - last_dt >= timedelta(minutes=interval_minutes)


def _anchor_if_due(config: dict[str, Any], state: dict[str, Any], now: datetime) -> None:
    """Execute legacy hash-batch anchoring when due (Zero Cost: no-op).

    Ejecuta anclaje de hashes si corresponde (Costo Cero: no-op).

    Arbitrum batch anchoring was removed; per-snapshot OTS anchoring via
    ``_anchor_snapshot``/``MultichainAnchor`` is the current mechanism. This
    function remains as a guarded no-op for legacy configs that still set
    ``arbitrum.enabled``.
    """
    arbitrum_config = config.get("arbitrum", {})
    if not arbitrum_config.get("enabled", False):
        return
    if not _has_private_key(arbitrum_config):
        logger.warning("anchor_skipped_missing_private_key")
        return

    interval_minutes = int(arbitrum_config.get("interval_minutes", 15))
    batch_size = int(arbitrum_config.get("batch_size", 19))
    if not _should_anchor(state, now, interval_minutes):
        return

    hashes = _read_hashes_for_anchor(batch_size)
    if len(hashes) < batch_size:
        logger.warning(
            "anchor_skipped_not_enough_hashes expected=%s actual=%s",
            batch_size,
            len(hashes),
        )
        return

    logger.info("anchor_skipped_arbitrum_removed")
    return


def _generate_and_upload_pdf(output_filename: str = "vigil_informe.pdf") -> str | None:
    """Run generate_report.py --upload and return the public URL printed to stdout.

    Ejecuta generate_report.py --upload y devuelve la URL publica impresa en stdout.
    """
    try:
        result = subprocess.run(
            [sys.executable, "scripts/generate_report.py", "--upload", "--sign", "--output", output_filename],
            capture_output=True,
            text=True,
            timeout=120,
        )
        for line in result.stdout.splitlines():
            if line.startswith("PDF uploaded:"):
                return line.split(":", 1)[1].strip()
        if result.returncode != 0:
            logger.warning("generate_report_failed stderr=%s", result.stderr[:300])
    except Exception as exc:  # noqa: BLE001
        logger.warning("generate_report_error error=%s", exc)
    return None


def run_pipeline(config: dict[str, Any]) -> None:
    """Execute the full resilient pipeline run.

    Bilingual: Ejecuta una corrida completa del pipeline resiliente.

    Notes:
        - Integrates rate_limiter + proxy_manager before each CNE HTTP request.
        - Runs secure_backup on successful scrape and in fail-safe finally flow.
        - Never breaks main loop due to backup/proxy hook failures.
    """
    now = utcnow()
    resilience_settings = load_resilience_settings(config)
    chaos_rng = build_chaos_rng(resilience_settings)
    state = load_state()
    checkpoint = load_pipeline_checkpoint()
    resilience_checkpoint = load_resilience_checkpoint()
    run_id = checkpoint.get("run_id") or resilience_checkpoint.get("run_id") or now.strftime("%Y%m%d%H%M%S")
    start_stage = "start"
    latest_snapshot: Path | None = None
    content_hash: str | None = None
    resume_stage = resilience_checkpoint.get("stage")
    resume_snapshot_name = resilience_checkpoint.get("latest_snapshot")
    if (
        resume_stage in RESILIENCE_STAGE_ORDER
        and resume_snapshot_name
        and resume_stage not in {"start", "healthcheck", "download"}
    ):
        candidate_snapshot = DATA_DIR / resume_snapshot_name
        if candidate_snapshot.exists():
            latest_snapshot = candidate_snapshot
            content_hash = resilience_checkpoint.get("last_content_hash")
            start_stage = resume_stage
            log_event(
                logger,
                logging.INFO,
                "pipeline_resume",
                run_id=run_id,
                stage=resume_stage,
                snapshot=resume_snapshot_name,
            )
    save_pipeline_checkpoint({"run_id": run_id, "stage": "start", "at": now.isoformat()})
    save_resilience_checkpoint(
        run_id,
        "start",
        latest_snapshot=latest_snapshot,
        content_hash=content_hash,
    )
    log_event(logger, logging.INFO, "pipeline_start", run_id=run_id)

    enable_backup: bool = bool(config.get("ENABLE_BACKUP", True))
    rate_limiter = get_rate_limiter()
    runtime_vital_config: dict[str, Any] = {**vital_signs.load_vital_signs_config("prod"), **config}
    consecutive_failures: int = 0
    scrape_status: dict[str, Any] = {
        "consecutive_failures": 0,
        "success_history": [],
        "latency_history": [],
        "hash_chain_valid": True,
        "high_pressure_since": None,
        "policy_block_since": None,
    }

    try:
        if should_run_stage("healthcheck", start_stage):
            save_pipeline_checkpoint({"run_id": run_id, "stage": "healthcheck", "at": utcnow().isoformat()})
            save_resilience_checkpoint(run_id, "healthcheck")
            maybe_inject_chaos_failure("healthcheck", resilience_settings, chaos_rng)
            waited = rate_limiter.wait()
            if waited > 0:
                log_event(logger, logging.DEBUG, "rate_limiter_waited", seconds=round(waited, 2))

            # Cumplimiento Ley Transparencia 170-2006: solo datos publicos agregados, rate-limits eticos siempre respetados
            predicted_mode = vital_signs.predict_mode(runtime_vital_config, scrape_status)
            if predicted_mode == "conservative":
                time.sleep(900)
            elif predicted_mode == "hibernation":
                try:
                    backup_state = secure_backup.backup_critical()
                    scrape_status["hash_chain_valid"] = bool(backup_state.get("hash_chain_valid", True))
                except Exception as backup_exc:  # noqa: BLE001
                    log_event(logger, logging.WARNING, "hibernation_backup_failed", error=str(backup_exc))
                time.sleep(3600)

            if float(scrape_status.get("request_pressure", 0.0)) > 8.0:
                config["max_concurrent_requests"] = 1

            proxy_dict, user_agent = proxy_manager.get_proxy_and_ua()
            request_headers = proxy_manager.get_proxy_ua_manager().build_request_headers(user_agent)
            proxy_url = (proxy_dict or {}).get("https")
            log_event(
                logger,
                logging.DEBUG,
                "proxy_ua_rotated",
                proxy=proxy_url or "direct",
                ua=user_agent[:60],
            )

            request_started_at = time.monotonic()
            status_code: int | None = None
            health_ok = False
            try:
                status_code = perform_cne_preflight_request(
                    config, proxy_dict, user_agent, request_headers=request_headers
                )
                health_ok = status_code < 400
                consecutive_failures = 0 if health_ok else consecutive_failures + 1
                _now_iso = utcnow().isoformat()
                state["cne_last_attempt_at"] = _now_iso
                state["cne_last_status_code"] = status_code
                if health_ok:
                    state["cne_last_successful_scrape_at"] = _now_iso
                    state.pop("cne_first_unreachable_at", None)
                    state["cne_consecutive_failures"] = 0
                else:
                    is_new_blackout = not state.get("cne_first_unreachable_at")
                    if is_new_blackout:
                        state["cne_first_unreachable_at"] = _now_iso
                        _trigger_emergency_publish(reason="cne_blackout_start")
                    state["cne_consecutive_failures"] = consecutive_failures
            except (
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                TimeoutError,
                ConnectionError,
            ) as exc:
                consecutive_failures += 1
                try:
                    proxy_manager.mark_proxy_bad(proxy_dict)
                except Exception as proxy_exc:  # noqa: BLE001
                    log_event(logger, logging.WARNING, "proxy_mark_bad_failed", error=str(proxy_exc))
                log_event(
                    logger,
                    logging.WARNING,
                    "healthcheck_request_exception",
                    run_id=run_id,
                    error=str(exc),
                )
                rate_limiter.notify_response(status_code, success=False)
                scrape_status = vital_signs.update_status_after_scrape(
                    scrape_status,
                    success=False,
                    latency=max(0.0, time.monotonic() - request_started_at),
                    status_code=status_code,
                    config=runtime_vital_config,
                )
                scrape_status["consecutive_failures"] = consecutive_failures
                vital_state = vital_signs.check_vital_signs(runtime_vital_config, scrape_status)
                log_event(
                    logger,
                    logging.WARNING,
                    "vital_signs_after_critical_exception",
                    run_id=run_id,
                    mode=vital_state.get("mode"),
                    recommended_delay=vital_state.get("recommended_delay_seconds"),
                )
            latency = max(0.0, time.monotonic() - request_started_at)
            rate_limiter.notify_response(status_code, success=bool(health_ok))

            if status_code in {429, 403} or (status_code is not None and 500 <= status_code <= 599):
                consecutive_failures += 1
                try:
                    proxy_manager.mark_proxy_bad(proxy_dict)
                except Exception as proxy_exc:  # noqa: BLE001
                    log_event(logger, logging.WARNING, "proxy_mark_bad_failed", error=str(proxy_exc))

            if consecutive_failures > 0:
                scrape_status = vital_signs.update_status_after_scrape(
                    scrape_status,
                    success=False,
                    latency=latency,
                    status_code=status_code,
                    config=runtime_vital_config,
                )
                scrape_status["consecutive_failures"] = consecutive_failures
                vital_state = vital_signs.check_vital_signs(runtime_vital_config, scrape_status)
                log_event(
                    logger,
                    logging.WARNING,
                    "vital_signs_after_failure",
                    run_id=run_id,
                    mode=vital_state.get("mode"),
                    recommended_delay=vital_state.get("recommended_delay_seconds"),
                )
            else:
                scrape_status = vital_signs.update_status_after_scrape(
                    scrape_status,
                    success=True,
                    latency=latency,
                    status_code=status_code,
                    config=runtime_vital_config,
                )

            download_cmd = [sys.executable, "scripts/download_and_hash.py"]
            if not health_ok:
                log_event(
                    logger,
                    logging.WARNING,
                    "healthcheck_failed_fallback_mock",
                    run_id=run_id,
                )
                download_cmd.append("--mock")

            if should_run_stage("download", start_stage):
                save_pipeline_checkpoint({"run_id": run_id, "stage": "download", "at": utcnow().isoformat()})
                save_resilience_checkpoint(run_id, "download")
                maybe_inject_chaos_failure("download", resilience_settings, chaos_rng)
                retry_config_path = config.get("retry_config_path") or os.getenv(
                    "RETRY_CONFIG_PATH", "config/prod/retry_config.yaml"
                )
                download_env = os.environ.copy()
                download_env["RETRY_CONFIG_PATH"] = retry_config_path
                run_command(download_cmd, "descarga + hash", env=download_env)

        max_json = resolve_max_json_limit(config)
        snapshots = build_snapshot_queue(max_json)
        if snapshots:
            process_snapshot_queue(
                snapshots,
                resilience_checkpoint,
                run_id=run_id,
            )

        if latest_snapshot is None:
            all_snaps = iter_all_snapshots(data_root=DATA_DIR)
            latest_snapshot = snapshots[-1] if snapshots else (all_snaps[-1] if all_snaps else None)
        if not latest_snapshot:
            print("[!] No se encontro snapshot para procesar")
            log_event(logger, logging.WARNING, "snapshot_missing", run_id=run_id)
            return

        content_hash = content_hash or compute_content_hash(latest_snapshot)
        if state.get("last_content_hash") == content_hash:
            state["last_run_at"] = now.isoformat()
            save_state(state)
            print("[i] Snapshot duplicado detectado, se omite procesamiento")
            log_event(logger, logging.INFO, "snapshot_duplicate", run_id=run_id)
            return

        state["last_content_hash"] = content_hash
        state["last_snapshot"] = latest_snapshot.name

        if should_run_stage("normalize", start_stage):
            save_pipeline_checkpoint({"run_id": run_id, "stage": "normalize", "at": utcnow().isoformat()})
            save_resilience_checkpoint(
                run_id,
                "normalize",
                latest_snapshot=latest_snapshot,
                content_hash=content_hash,
            )
            maybe_inject_chaos_failure("normalize", resilience_settings, chaos_rng)
            if should_normalize(latest_snapshot):
                run_command(
                    [sys.executable, "scripts/normalize_presidential.py"],
                    "normalizacion",
                )
            else:
                print("[i] Normalizacion omitida: estructura no compatible")
                log_event(logger, logging.INFO, "normalize_skipped", run_id=run_id)

        if should_run_stage("analyze", start_stage):
            save_pipeline_checkpoint({"run_id": run_id, "stage": "analyze", "at": utcnow().isoformat()})
            save_resilience_checkpoint(
                run_id,
                "analyze",
                latest_snapshot=latest_snapshot,
                content_hash=content_hash,
            )
            maybe_inject_chaos_failure("analyze", resilience_settings, chaos_rng)
            run_command([sys.executable, "scripts/analyze_rules.py"], "analisis")

        anomalies_path = Path("anomalies_report.json")
        anomalies = []
        if anomalies_path.exists():
            anomalies = json.loads(anomalies_path.read_text(encoding="utf-8"))

        critical_anomalies = filter_critical_anomalies(anomalies, config)
        alerts = build_alerts(critical_anomalies, severity="CRITICAL")
        (ANALYSIS_DIR / "alerts.json").write_text(json.dumps(alerts, indent=2), encoding="utf-8")
        emit_critical_alerts(critical_anomalies, config, run_id=run_id)
        if critical_anomalies:
            _trigger_emergency_publish(reason="critical_anomaly")

        if should_run_stage("report", start_stage):
            save_pipeline_checkpoint({"run_id": run_id, "stage": "report", "at": utcnow().isoformat()})
            save_resilience_checkpoint(
                run_id,
                "report",
                latest_snapshot=latest_snapshot,
                content_hash=content_hash,
            )
            maybe_inject_chaos_failure("report", resilience_settings, chaos_rng)
            if should_generate_report(state, now):
                run_command([sys.executable, "scripts/summarize_findings.py"], "reportes")
                state["last_report_at"] = now.isoformat()
                pdf_url = _generate_and_upload_pdf("vigil_informe_nacional.pdf")
                if pdf_url:
                    state["last_report_pdf_url"] = pdf_url
            else:
                print("[i] Reporte omitido por cadencia")
                log_event(logger, logging.INFO, "report_skipped", run_id=run_id)

        if should_run_stage("anchor", start_stage):
            save_resilience_checkpoint(
                run_id,
                "anchor",
                latest_snapshot=latest_snapshot,
                content_hash=content_hash,
            )
            maybe_inject_chaos_failure("anchor", resilience_settings, chaos_rng)
            _anchor_snapshot(config, state, now, latest_snapshot)
            _anchor_if_due(config, state, now)

        _publish_forensics(
            config,
            now,
            extra_meta=(
                {"report_pdf_url": state.get("last_report_pdf_url")} if state.get("last_report_pdf_url") else None
            ),
        )

        scrape_status = vital_signs.update_status_after_scrape(
            scrape_status,
            success=True,
            latency=0.0,
            status_code=200,
            config=runtime_vital_config,
        )
        update_daily_summary(state, now, len(anomalies))
        state["last_run_at"] = now.isoformat()
        save_state(state)
        clear_pipeline_checkpoint()
        clear_resilience_checkpoint()

        if enable_backup:
            try:
                backup_result = secure_backup.backup_critical()
                log_event(
                    logger,
                    logging.INFO,
                    "post_scrape_backup",
                    run_id=run_id,
                    local=backup_result.get("local", False),
                    files=len(backup_result.get("files_backed_up", [])),
                )
            except Exception as backup_exc:  # noqa: BLE001
                log_event(logger, logging.WARNING, "post_scrape_backup_failed", error=str(backup_exc))

        log_event(logger, logging.INFO, "pipeline_complete", run_id=run_id)
    except Exception as exc:  # noqa: BLE001
        log_event(
            logger,
            logging.ERROR,
            "pipeline_failed",
            run_id=run_id,
            error=str(exc),
        )
        save_resilience_checkpoint(
            run_id,
            checkpoint.get("stage") or "error",
            latest_snapshot=latest_snapshot,
            content_hash=content_hash,
            error=str(exc),
        )
        raise
    finally:
        if enable_backup:
            try:
                secure_backup.backup_critical()
            except Exception as backup_exc:  # noqa: BLE001
                log_event(logger, logging.WARNING, "final_backup_failed", error=str(backup_exc))


def safe_run_pipeline(config: dict[str, Any], security_manager: DefensiveSecurityManager | None = None) -> bool:
    """Run pipeline with auto-resume on network failures.

    Ejecuta pipeline con auto-reanudación en fallas de red.
    """
    # Prevent concurrent runs (e.g. GitHub Actions schedule + workflow_dispatch overlap)
    _lock_fd = open("/tmp/vigil_pipeline.lock", "w")  # noqa: SIM115  # nosec B108
    try:
        fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log_event(logger, logging.WARNING, "pipeline_already_running_skipping")
        return False

    resilience_settings = load_resilience_settings(config)
    auto_resume = build_auto_resume_settings(resilience_settings)

    _network_excs = (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        TimeoutError,
        ConnectionError,
    )

    def _should_retry(exc: BaseException) -> bool:
        """True if the exception warrants a retry. / True si la excepción justifica un reintento."""
        if not auto_resume["enabled"]:
            return False
        retry_on = auto_resume["retry_on"]
        if isinstance(exc, _network_excs):
            return retry_on in {"any", "network"}
        return retry_on == "any"

    def _after_failure(retry_state: Any) -> None:
        """Log and checkpoint every failure. / Registra y checkpoint en cada fallo."""
        exc = retry_state.outcome.exception()
        if exc is None:
            return
        checkpoint = load_pipeline_checkpoint()
        run_id = checkpoint.get("run_id", utcnow().strftime("%Y%m%d%H%M%S"))
        stage = checkpoint.get("stage")
        is_network = isinstance(exc, _network_excs)
        log_event(
            logger,
            logging.ERROR,
            "pipeline_network_failure" if is_network else "pipeline_failure",
            run_id=run_id,
            stage=stage or "unknown",
            error=str(exc),
        )
        if security_manager:
            if is_network:
                security_manager.record_http_error(timeout=True)
            security_manager.record_log_error()
        save_resilience_checkpoint(run_id, stage, error=str(exc))

    def _before_sleep(retry_state: Any) -> None:
        """Log the upcoming wait. / Registra la espera antes del siguiente intento."""
        checkpoint = load_pipeline_checkpoint()
        run_id = checkpoint.get("run_id", utcnow().strftime("%Y%m%d%H%M%S"))
        log_event(
            logger,
            logging.WARNING,
            "pipeline_auto_resume_wait",
            run_id=run_id,
            attempt=retry_state.attempt_number,
            delay_seconds=retry_state.next_action.sleep,
        )

    try:
        for attempt in Retrying(
            stop=stop_after_attempt(auto_resume["max_attempts"]),
            wait=wait_exponential(
                multiplier=auto_resume["backoff_base_seconds"],
                max=auto_resume["backoff_max_seconds"],
                min=0,
                exp_base=2,
            ),
            retry=retry_if_exception(_should_retry),
            after=_after_failure,
            before_sleep=_before_sleep,
            sleep=time.sleep,
            reraise=True,
        ):
            with attempt:
                run_pipeline(config)
        return True
    except Exception:  # noqa: BLE001
        return False


def _make_swarm_attack_hook():
    """Build the swarm-wide attack finding broadcast hook, if configured.

    Construye el hook de difusion de hallazgos de ataque al swarm, si esta
    configurado.

    Returns:
        A callable hook for ``AttackLogConfig.finding_broadcast_hook``, or
        ``None`` when swarm gossip broadcasting is not configured (Zero
        Cost default: local-only attack logging, no broadcast).
    """
    return None


def main():
    """/** Punto de entrada principal. / Main entry point. **"""
    parser = argparse.ArgumentParser(
        description="Pipeline Proyecto VIGIL: descarga -> normaliza -> hash -> analisis -> reportes -> alertas"
    )
    parser.add_argument("--once", action="store_true", help="Ejecuta una sola vez y sale")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Ejecuta inmediatamente antes del scheduler",
    )
    args = parser.parse_args()
    config = load_pipeline_config()
    attack_config = AttackLogConfig.from_yaml(ATTACK_CONFIG_PATH)
    attack_config.finding_broadcast_hook = _make_swarm_attack_hook()
    attack_logbook = AttackForensicsLogbook(attack_config)
    attack_logbook.start()
    honeypot = HoneypotServer(attack_config, attack_logbook)
    honeypot.start()
    core_logger.register_attack_logbook(attack_logbook)
    security_manager = DefensiveSecurityManager(SecurityConfig.from_yaml(SECURITY_CONFIG_PATH), logger=logger)
    security_manager.register_signal_handlers()
    security_manager.start_honeypot()
    advanced_security_manager = load_manager(ADVANCED_SECURITY_CONFIG_PATH)
    advanced_security_manager.start()

    # Start background encrypted backup scheduler (every 30 min) /
    # Iniciar programador de respaldo cifrado en segundo plano (cada 30 min)
    backup_scheduler = BackupScheduler(interval_seconds=1800)
    backup_scheduler.start()

    def _guarded_run() -> bool:
        attack_logbook.log_connection_snapshot()
        triggers = security_manager.detect_hostile_conditions()
        if triggers:
            security_manager.activate_defensive_mode(
                triggers,
                snapshot_state=build_defensive_state_snapshot(),
            )
        advanced_security_manager.on_poll_cycle()
        return safe_run_pipeline(config, security_manager=security_manager)

    try:
        master_status = normalize_master_switch(config.get("master_switch"))
        print(f"[i] MASTER SWITCH: {master_status}")
        if not is_master_switch_on(config):
            print("[!] Ejecución detenida por switch maestro (OFF)")
            return

        # --- FASE 2: Verificación de cadena de custodia al arranque ---
        custody_config = config.get("custody", {})
        if custody_config.get("verify_on_startup", False):
            print("[+] Verificando cadena de custodia al arranque...")
            log_event(logger, logging.INFO, "custody_verification_start")
            try:
                custody_report = run_startup_verification(
                    hash_dir=HASH_DIR,
                    anchor_log_dir=ANCHOR_LOG_DIR,
                    verify_anchors=custody_config.get("verify_anchors_on_startup", False),
                    verify_signatures=custody_config.get("verify_signatures", True),
                    max_anchor_checks=int(custody_config.get("max_anchor_checks", 5)),
                )
                report_path = DATA_DIR / "custody_verification.json"
                report_path.write_text(
                    json.dumps(custody_report.to_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                if custody_report.overall_valid:
                    print(f"[+] Cadena de custodia válida ({custody_report.chain_result.verified_links} eslabones)")
                    log_event(
                        logger,
                        logging.INFO,
                        "custody_verification_passed",
                        links=(custody_report.chain_result.verified_links if custody_report.chain_result else 0),
                    )
                else:
                    print("[!] ADVERTENCIA: Cadena de custodia con inconsistencias")
                    log_event(
                        logger,
                        logging.WARNING,
                        "custody_verification_warning",
                        errors=(custody_report.chain_result.errors if custody_report.chain_result else []),
                        sig_failures=custody_report.signature_failures,
                    )
            except Exception as exc:
                print(f"[!] Error en verificación de custodia: {exc}")
                log_event(logger, logging.ERROR, "custody_verification_failed", error=str(exc))

        if args.once:
            update_heartbeat(status="manual_once")
            try:
                _guarded_run()
            except DefensiveShutdown:
                update_heartbeat(status="defensive_shutdown")
                raise SystemExit(0)
            update_heartbeat(status="manual_once_completed")
            return

        if args.run_now:
            update_heartbeat(status="manual_run_now")
            try:
                _guarded_run()
            except DefensiveShutdown:
                update_heartbeat(status="defensive_shutdown")
                raise SystemExit(0)

        scheduler = BlockingScheduler(timezone="UTC")
        scheduler.add_job(update_heartbeat, "interval", minutes=1)
        scheduler.add_job(_guarded_run, CronTrigger(minute=0))
        print("[+] Scheduler activo: ejecución horaria en minuto 00 UTC")
        scheduler.start()
    finally:
        backup_scheduler.stop()
        advanced_security_manager.shutdown()
        honeypot.stop()
        attack_logbook.stop()


if __name__ == "__main__":
    main()
