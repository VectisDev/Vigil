"""
CENTINEL — Pipeline Runner
===========================
Punto de entrada del pipeline de auditoría electoral.
Electoral audit pipeline entry point.

Functions:
  - resolve_poll_interval_seconds: Return polling interval from config
  - resolve_poll_jitter_factor:    Return jitter factor from config
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


logger = logging.getLogger("centinel.pipeline")


def log_event(log: logging.Logger, level: int, event: str, **kwargs: Any) -> None:
    """Structured log event. / Evento de log estructurado."""
    log.log(level, event, extra=kwargs)


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

    # Submit Merkle root to Bitcoin via OpenTimestamps (T3 external anchor)
    ots_proof = submit_to_opentimestamps(root_hash)
    if ots_proof is not None:
        ots_dir = ANCHOR_LOG_DIR / "ots"
        ots_dir.mkdir(parents=True, exist_ok=True)
        ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ots_path = ots_dir / f"{ts_slug}_{root_hash[:12]}.ots"
        ots_path.write_bytes(ots_proof.raw_proof)
        proof_meta = ots_dir / f"{ts_slug}_{root_hash[:12]}.json"
        proof_meta.write_text(json.dumps(ots_proof.to_dict(), indent=2), encoding="utf-8")
        logger.info(
            "ots_proof_saved path=%s server=%s",
            ots_path,
            ots_proof.timestamp_server,
        )
    else:
        logger.warning("ots_proof_unavailable root_hash=%s", root_hash[:16])


def main():
    """/** Punto de entrada principal. / Main entry point. **"""
    parser = argparse.ArgumentParser(
        description="Pipeline Proyecto C.E.N.T.I.N.E.L.: descarga → normaliza → hash → análisis → reportes → alertas"
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
