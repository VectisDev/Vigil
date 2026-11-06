#!/usr/bin/env python3
"""
Export a static snapshot.json consumed by the public panel.

Reads pipeline-generated files and writes web/data/snapshot.json.
No network calls. Designed to run after each pipeline cycle in CI.

Usage:
  python scripts/export_static_snapshot.py [--root .]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _read_json(path: Path) -> dict:
    """Lee JSON devolviendo {} si falta o es ilegible.

    English: Read JSON, returning {} when missing or unreadable. Prefer
    _read_json_checked() where the difference matters: "absent" and "corrupt"
    are different facts and must not both be published as healthy emptiness.
    """
    data, _ = _read_json_checked(path)
    return data


def _read_json_checked(path: Path) -> tuple[dict, str]:
    """Devuelve (datos, estado) con estado en {"ok", "missing", "unreadable"}.

    English: Return (data, status) where status is one of "ok", "missing" or
    "unreadable", so the caller can tell a file that was never written from one
    that is corrupt.
    """
    if not path.exists():
        return {}, "missing"
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, "unreadable"
    return (parsed if isinstance(parsed, dict) else {}), "ok"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _blackout_hash(endpoint: str, blackout_since: str, error_type: str | None) -> str:
    raw = f"{endpoint}|{blackout_since}|{error_type or 'unknown'}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _build_cne_status(state: dict, endpoint: str) -> dict:
    consecutive = int(state.get("cne_consecutive_failures", 0))

    last_ok = state.get("cne_last_successful_scrape_at")
    last_attempt = state.get("cne_last_attempt_at")

    # Sin ningun intento registrado no se puede afirmar alcanzabilidad: el valor
    # es None ("desconocido"), nunca True. Antes, cero intentos se codificaba
    # como salud plena porque consecutive_failures valia 0 por defecto.
    # With no recorded attempt we cannot assert reachability: the value is None
    # ("unknown"), never True. Previously zero attempts was encoded as full
    # health because consecutive_failures defaulted to 0.
    if not last_attempt:
        reachable = None
    else:
        reachable = consecutive == 0
    first_unreachable = state.get("cne_first_unreachable_at")

    blackout_minutes = 0
    blackout_hash_val = None

    if reachable is False and first_unreachable:
        try:
            since_dt = datetime.fromisoformat(first_unreachable.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            blackout_minutes = max(0, int((now_dt - since_dt).total_seconds() / 60))
        except Exception:
            # Malformed timestamp: keep blackout_minutes at 0.
            pass
        blackout_hash_val = _blackout_hash(endpoint, first_unreachable, state.get("cne_last_error_type"))

    return {
        "reachable": reachable,
        "last_successful_fetch": last_ok,
        "last_attempt": last_attempt,
        "consecutive_failures": consecutive,
        "blackout_minutes": blackout_minutes,
        "blackout_since": first_unreachable if reachable is False else None,
        "error_type": state.get("cne_last_error_type") if reachable is False else None,
        "blackout_hash": blackout_hash_val,
    }


def _build_chain(state: dict, hash_dir: Path) -> dict:
    latest_hash = ""
    merkle_root = ""
    chain_length = 0

    all_hashes = sorted(hash_dir.glob("*.json")) if hash_dir.is_dir() else []
    if all_hashes:
        latest = _read_json(all_hashes[-1])
        latest_hash = latest.get("chained_hash") or latest.get("hash") or ""
        merkle_root = latest.get("merkle_root", "")
        chain_length = len(all_hashes)

    # Also check state for richer info
    recent = state.get("hashes", [])
    if recent and not latest_hash:
        latest_hash = recent[0].get("chained_hash") or recent[0].get("hash") or ""

    return {
        "latest_hash": latest_hash,
        "merkle_root": merkle_root,
        "chain_length": chain_length,
        "ots_status": state.get("ots_status", "pending"),
    }


def _build_national(snapshot: dict) -> dict:
    if not snapshot:
        return {}
    return {
        "actas_escrutadas": snapshot.get("actas_escrutadas", 0),
        "actas_total": snapshot.get("actas_total", 0),
        "total_votos": snapshot.get("total_votos", 0),
        "candidatos": snapshot.get("candidatos", {}),
        "source": snapshot.get("source", ""),
        "timestamp": snapshot.get("timestamp", ""),
    }


def _build_departments(snapshot: dict) -> dict:
    depts = snapshot.get("departamentos", [])
    if not isinstance(depts, list):
        return {}
    out = {}
    for d in depts:
        code = d.get("codigo") or d.get("nombre", "").upper().replace(" ", "_")
        out[code] = {
            "nombre": d.get("nombre", code),
            "actas_escrutadas": d.get("actas_escrutadas", 0),
            "actas_total": d.get("actas_total", 0),
            "total_votos": d.get("total_votos", 0),
            "candidatos": d.get("candidatos", {}),
        }
    return out


def _build_coverage(snapshot: dict) -> dict:
    total = snapshot.get("actas_total", 0)
    scrutinized = snapshot.get("actas_escrutadas", 0)
    pct = round(scrutinized / total * 100, 2) if total else 0.0
    return {
        "actas_escrutadas": scrutinized,
        "actas_total": total,
        "pct_coverage": pct,
    }


def _build_replay(out_dir: Path) -> dict:
    """Lo que el replay dejo, y nada que no haya dejado.

    English: what the replay left behind, and nothing it did not.

    `merkle_verified` solo es cierto si `replay_pipeline.py` recalculo la raiz
    desde las capturas y coincidio con la comprometida; ese script falla cuando
    no coincide, asi que el manifiesto no puede afirmarlo en falso sin que el
    workflow haya salido en rojo antes.
    """
    manifest_path = out_dir / "replay_manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # Un manifiesto ilegible no se convierte en un manifiesto ausente en
        # silencio: no es evidencia, y el estado lo reflejara.
        # English: an unreadable manifest is not silently treated as absent.
        return {"merkle_verified": False, "error": "manifiesto ilegible"}
    if not isinstance(manifest, dict):
        return {"merkle_verified": False, "error": "manifiesto con forma inesperada"}
    return {
        "dataset": manifest.get("dataset"),
        "files": manifest.get("files"),
        "merkle_root": manifest.get("merkle_root"),
        "merkle_verified": bool(manifest.get("merkle_verified")),
        "ots_proof": manifest.get("ots_proof"),
        "alerts": manifest.get("alerts"),
        "generated_at": manifest.get("generated_at"),
        "note": manifest.get("note"),
    }


def _latest_snapshot(data_dir: Path) -> dict:
    candidates = sorted(
        [p for p in data_dir.glob("*.json") if p.stem not in ("pipeline_state", "heartbeat", "custody_verification")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    # Skip temp/mock subdirectories; only files directly in data_dir
    direct = [p for p in candidates if p.parent == data_dir]
    if direct:
        return _read_json(direct[0])
    return {}


def _build_endpoint_health(root: Path) -> dict:
    empty = {"available": False, "total": 0, "online": 0, "degraded": 0, "offline": 0, "endpoints": []}
    try:
        sys.path.insert(0, str(root / "src"))
        from vigil.sync.forensics_publisher import build_endpoint_health_block

        return build_endpoint_health_block(root / "config" / "prod" / "endpoints.yaml")
    except Exception:
        return empty


def export_snapshot(
    root: Path = Path("."),
    declared_mode: str | None = None,
    mode_reason: str = "",
) -> Path:
    """Escribe `web/data/snapshot.json`.

    `declared_mode` viene de `.github/scripts/resolve_mode.py`, el unico sitio
    donde se decide que esta haciendo el nodo. Sin el, el exportador se comporta
    como antes: util para una ejecucion local suelta, no para un workflow.

    English: `declared_mode` comes from `resolve_mode.py`, the single place
    where the node's state is decided. Without it the exporter behaves as
    before, which suits an ad-hoc local run but not a workflow.
    """
    data_dir = root / "data"
    hash_dir = root / "hashes"
    analysis_dir = root / "analysis"
    out_dir = root / "web" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    state, state_status = _read_json_checked(data_dir / "pipeline_state.json")
    alerts_raw = _read_json(analysis_dir / "alerts.json")
    alerts = alerts_raw if isinstance(alerts_raw, list) else alerts_raw.get("alerts", [])
    snapshot = _latest_snapshot(data_dir)

    endpoint = "https://resultados2029.cne.hn/"
    try:
        ep_cfg = _read_json(root / "config" / "prod" / "endpoints.yaml")
        endpoint = ep_cfg.get("cne", {}).get("main_url", endpoint)
    except Exception:
        # Missing or unreadable endpoints config: keep the default endpoint.
        pass

    forensics_path = analysis_dir / "forensics_latest.json"
    forensics = _read_json(forensics_path) if forensics_path.exists() else {}

    chain = _build_chain(state, hash_dir)
    cne_status = _build_cne_status(state, endpoint)

    # El exportador nunca publica un documento que afirme alcanzabilidad,
    # cobertura o estado de cadena que no midio. Si el pipeline no dejo estado y
    # no hay cadena ni snapshot, eso es ausencia de datos y se declara como tal.
    # The exporter never publishes a document asserting reachability, coverage or
    # chain state it did not measure. If the pipeline left no state and there is
    # no chain and no snapshot, that is absence of data and is declared as such.
    # El replay deja su propia evidencia, y es la mas fuerte de las tres: una
    # raiz de Merkle recalculada desde los archivos y coincidente con la que
    # esta anclada en Bitcoin. Un pipeline_state.json solo dice que el pipeline
    # corrio; esto dice que los datos son los mismos que se anclaron.
    # English: the replay leaves its own evidence, and it is the strongest of
    # the three: a Merkle root recomputed from the files that matches the one
    # anchored in Bitcoin. A pipeline_state.json only says the pipeline ran.
    replay = _build_replay(out_dir)

    # Las dos evidencias se cuentan por separado a proposito. Reproducir un
    # conjunto verificado NO es haber capturado nada: si se sumaran, bastaria
    # con distribuir el fixture para que un nodo que declara LIVE pareciera
    # tener datos. Es la misma clase de mentira que `reachable: true` sin medir.
    # English: the two kinds of evidence are counted separately on purpose.
    # Reproducing a verified dataset is NOT having captured anything: were they
    # pooled, shipping the fixture would be enough to make a node that declares
    # LIVE look like it holds data.
    has_capture_evidence = bool(state) or chain["chain_length"] > 0 or bool(snapshot)
    has_replay_evidence = bool(replay and replay.get("merkle_verified"))
    declared = (declared_mode or "").strip().upper()

    # Un nodo sin datos puede estar roto o estar legitimamente inactivo, y las
    # dos cosas se veian igual: ausencia de evidencia era siempre NO_DATA y
    # salida en rojo. Pero entre elecciones no hay nada que capturar, asi que
    # ese rojo seria permanente, y un rojo permanente ensena a ignorar los
    # rojos. El modo declarado es lo que las separa.
    # English: a node with no data may be broken or legitimately idle, and both
    # looked identical: absence of evidence always meant NO_DATA and a red exit.
    # Between elections there is nothing to collect, so that red would be
    # permanent -- and a permanent red teaches people to ignore reds. The
    # declared mode is what tells the two apart.
    if declared == "ARMED":
        status = "ARMED"
        status_reason = mode_reason or "a la espera de eleccion; sin intentos de captura"
    elif declared == "REPLAY" and (has_capture_evidence or has_replay_evidence):
        status = "REPLAY"
        status_reason = mode_reason or "reproduccion de un conjunto verificado; no es captura en vivo"
    elif declared == "REPLAY":
        # REPLAY declarado y sin datos SI es un fallo: el replay debia
        # producirlos. El detector sigue disparando donde corresponde.
        # English: REPLAY declared with no data IS a failure: the replay was
        # supposed to produce them. The detector still fires where it should.
        status = "NO_DATA"
        status_reason = "modo REPLAY declarado pero el replay no produjo datos verificados"
    elif not has_capture_evidence:
        status = "NO_DATA"
        status_reason = f"pipeline_state.json {state_status}; chain empty; no snapshot in {data_dir}"
    elif cne_status["reachable"] is False:
        status = "DEGRADED"
        status_reason = f"source unreachable ({cne_status['consecutive_failures']} consecutive failures)"
    elif cne_status["reachable"] is None:
        status = "DEGRADED"
        status_reason = "no fetch attempt recorded"
    else:
        status = "MONITORING"
        status_reason = ""

    result = {
        "schema_version": 1,
        "generated_at": _utcnow(),
        "status": status,
        "status_reason": status_reason,
        "declared_mode": declared or None,
        "cne_status": cne_status,
        "chain": chain,
        "national": _build_national(snapshot),
        "departments": _build_departments(snapshot),
        "forensics": forensics,
        "alerts": alerts[:50],
        "coverage": _build_coverage(snapshot),
        "report_pdf_url": state.get("last_report_pdf_url"),
        "endpoint_health": _build_endpoint_health(root),
        "replay": replay,
    }

    out_path = out_dir / "snapshot.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export static snapshot.json for the public panel.")
    parser.add_argument("--root", default=".", help="Repository root (default: cwd)")
    parser.add_argument(
        "--mode",
        default=None,
        choices=["REPLAY", "ARMED", "LIVE"],
        help="Modo efectivo, tal como lo resuelve .github/scripts/resolve_mode.py.",
    )
    parser.add_argument("--mode-reason", default="", help="Motivo legible del modo.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out = export_snapshot(root, declared_mode=args.mode, mode_reason=args.mode_reason)
    written, _ = _read_json_checked(out)
    status = written.get("status", "NO_DATA")
    print(f"Exported: {out} (status={status})")

    # Salir distinto de cero cuando no hay nada que publicar, para que el
    # workflow falle en rojo en vez de commitear un documento vacio que aparenta
    # salud. Sin esto, un pipeline roto es indistinguible de un pipeline inactivo.
    # Exit non-zero when there is nothing to publish, so the workflow goes red
    # instead of committing an empty document that looks healthy. Without this a
    # broken pipeline is indistinguishable from an idle one.
    if status == "NO_DATA":
        print(f"NO_DATA: {written.get('status_reason', '')}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
