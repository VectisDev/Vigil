#!/usr/bin/env python3
"""
======================== ÍNDICE / INDEX ========================
1. Propósito / Purpose
2. El aserto que lo sostiene todo / The assert that holds it up
3. Salidas / Outputs

======================== ESPAÑOL ========================
Archivo: `scripts/replay_pipeline.py`.

Reproduce el conjunto verificado de Honduras 2025 a través del motor real y
deja el panel de replay con datos auténticos.

Por qué existe: no hay elección que vigilar hasta 2029, así que el día uno de
cualquier despliegue sería un panel vacío. Pero el repositorio ya contiene 64
capturas reales de una elección disputada, con su raíz de Merkle confirmada en
Bitcoin por tres calendarios independientes. Reproducir eso en la máquina de
quien despliega demuestra la cadena de confianza completa, con datos reales y
**sin una sola petición al servidor de nadie**.

El aserto central: la raíz recalculada debe coincidir con la comprometida en
`MERKLE_ROOT_HN2025.txt`. Si no coincide, esto falla en rojo. Ese aserto es la
prueba de punta a punta; sin él, el replay sería una animación bonita.

No hace llamadas de red. El anclaje ya está hecho y comprometido; aquí solo se
recalcula y se compara.

======================== ENGLISH ========================
File: `scripts/replay_pipeline.py`.

Replays the verified Honduras 2025 dataset through the real engine and leaves
the replay panel holding authentic data.

Why it exists: there is no election to watch until 2029, so day one of any
deployment would be an empty panel. But the repository already holds 64 real
captures from a disputed election, with a Merkle root confirmed on Bitcoin by
three independent calendars. Reproducing that on the deployer's own machine
demonstrates the whole trust chain, with real data and **without a single
request to anyone's server**.

The central assert: the recomputed root must equal the one committed in
`MERKLE_ROOT_HN2025.txt`. On mismatch this fails red. That assert is the
end-to-end proof; without it the replay would be a pretty animation.

Makes no network calls. The anchoring is already done and committed; this only
recomputes and compares.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
for candidate in (REPO_ROOT, REPO_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from vigil.core.anchoring import _merkle_root  # noqa: E402

DEFAULT_DATASET = REPO_ROOT / "tests" / "fixtures" / "hnd_2025"
DEFAULT_OUT = REPO_ROOT / "web" / "data"
ROOT_FILE = "MERKLE_ROOT_HN2025.txt"


def parse_timestamp_from_filename(filename: str) -> datetime:
    """La marca de tiempo vive en el nombre del archivo, no en el payload.

    English: the timestamp lives in the filename, not in the payload. The CNE
    response carries no timestamp of its own, which is a documented limitation
    of this dataset and the reason the panel must not present it as a live feed.
    """
    match = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{2})_(\d{2})_(\d{2})", filename)
    if not match:
        raise ValueError(f"No se puede extraer la marca de tiempo de {filename!r}")
    date_str, hour, minute, second = match.groups()
    return datetime.fromisoformat(f"{date_str}T{hour}:{minute}:{second}+00:00")


def _to_int(value: object) -> int:
    """'1,027,090' -> 1027090. El CNE publica numeros como texto con comas."""
    if value is None:
        return 0
    text = str(value).replace(",", "").replace(" ", "").strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def expected_root(dataset: Path) -> str:
    """Lee la raiz comprometida del archivo que la acompana."""
    path = dataset / ROOT_FILE
    if not path.exists():
        raise FileNotFoundError(f"Falta {path}, que contiene la raiz comprometida")
    match = re.search(r"Merkle root \(SHA-256\):\s*([0-9a-f]{64})", path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"No se encuentra la raiz de Merkle en {path}")
    return match.group(1)


def build_snapshot_record(index: int, path: Path, raw: dict, captured_at: datetime) -> dict:
    """Traduce una captura del CNE a lo que consume el panel de replay."""
    stats = raw.get("estadisticas") or {}
    actas = stats.get("totalizacion_actas") or {}
    votos = stats.get("distribucion_votos") or {}
    estado = stats.get("estado_actas_divulgadas") or {}

    validos = _to_int(votos.get("validos"))
    nulos = _to_int(votos.get("nulos"))
    blancos = _to_int(votos.get("blancos"))

    return {
        "id": index,
        "captured_at": captured_at.isoformat(),
        # Todas las capturas de este conjunto son del agregado nacional.
        "dept_code": "Nacional",
        "source": "hnd_2025",
        "source_file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "raw_json": {
            "totalVotes": validos + nulos + blancos,
            "actasEscrutadas": _to_int(actas.get("actas_divulgadas")),
            "actasTotal": _to_int(actas.get("actas_totales")),
            "votosValidos": validos,
            "votosNulos": nulos,
            "votosBlancos": blancos,
            "actasCorrectas": _to_int(estado.get("actas_correctas")),
            "actasInconsistentes": _to_int(estado.get("actas_inconsistentes")),
            "resultados": [
                {
                    "partido": item.get("partido"),
                    "candidato": item.get("candidato"),
                    "votos": _to_int(item.get("votos")),
                    "porcentaje": item.get("porcentaje"),
                }
                for item in (raw.get("resultados") or [])
            ],
        },
    }


def run_detectors(dataset: Path, files: list[Path], tmp_dir: Path) -> list[dict]:
    """Ejecuta el motor de deteccion real sobre las capturas.

    English: runs the real detection engine over the captures. Importing the
    tracker lazily keeps this script usable for the Merkle check alone when the
    heavier dependencies are not installed.
    """
    from auditor.inconsistent_acts import InconsistentActsTracker

    tracker = InconsistentActsTracker(
        config_path=tmp_dir / "replay_key.json",
        runtime_config_path=tmp_dir / "replay_config.json",
        blackout_gap_minutes=30,
        max_resolution_rate=10.0,
        bulk_resolution_threshold=200,
        stagnation_cycles_threshold=4,
        prolonged_stagnation_cycles=8,
    )
    for path in files:
        tracker.load_snapshot(
            json.loads(path.read_text(encoding="utf-8")),
            parse_timestamp_from_filename(path.name),
        )
    anomalies = tracker.detect_anomalies()

    # detect_anomalies devuelve dataclasses Anomaly, no diccionarios. Un filtro
    # por isinstance(dict) las descarta TODAS en silencio, y el panel se queda
    # con cero alertas pareciendo que no hubo hallazgos. Convertir, y fallar si
    # aparece algo que no se sabe convertir, en vez de tirarlo.
    # English: detect_anomalies returns Anomaly dataclasses, not dicts. An
    # isinstance(dict) filter silently drops ALL of them and the panel ends up
    # with zero alerts, looking like there were no findings. Convert, and fail
    # on anything unconvertible rather than discarding it.
    out: list[dict] = []
    for anomaly in anomalies:
        if is_dataclass(anomaly) and not isinstance(anomaly, type):
            record = asdict(anomaly)
        elif isinstance(anomaly, dict):
            record = dict(anomaly)
        else:
            raise TypeError(f"Anomalia de tipo inesperado: {type(anomaly).__name__}")

        # El panel agrupa por marca de tiempo; necesita ISO, no datetime.
        stamp = record.get("timestamp")
        if isinstance(stamp, datetime):
            record["timestamp"] = stamp.isoformat()
        out.append(record)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce el conjunto verificado HN-2025.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--skip-detectors",
        action="store_true",
        help="Solo recalcula y compara la raiz; util para una comprobacion rapida.",
    )
    args = parser.parse_args()

    dataset = Path(args.dataset).resolve()
    out_dir = Path(args.out).resolve()

    files = sorted(dataset.glob("*.json"))
    if not files:
        print(f"ERROR: no hay capturas .json en {dataset}", file=sys.stderr)
        return 1

    print(f"Capturas: {len(files)} en {dataset}")

    # ── El aserto que sostiene todo el replay ──────────────────────────────
    # Mismas hojas y mismo orden que vigil.core.anchoring: sha256 de cada
    # archivo, ordenados por ruta. Si esto diverge, la raiz no coincide y el
    # replay falla, que es exactamente lo que debe pasar.
    leaves = [hashlib.sha256(path.read_bytes()).hexdigest() for path in files]
    computed = _merkle_root(leaves.copy())
    committed = expected_root(dataset)

    print(f"Raiz recalculada: {computed}")
    print(f"Raiz comprometida: {committed}")
    if computed != committed:
        print(
            "ERROR: la raiz recalculada NO coincide con la comprometida.\n"
            "       El conjunto de datos o el algoritmo han cambiado. El replay\n"
            "       no puede afirmar que reproduce un anclaje verificado.",
            file=sys.stderr,
        )
        return 1
    print("COINCIDE — el anclaje a Bitcoin cubre exactamente estas capturas.")

    # ── Registros para el panel ────────────────────────────────────────────
    records = []
    for index, path in enumerate(files, start=1):
        raw = json.loads(path.read_text(encoding="utf-8"))
        records.append(build_snapshot_record(index, path, raw, parse_timestamp_from_filename(path.name)))

    out_dir.mkdir(parents=True, exist_ok=True)
    snapshots_path = out_dir / "replay_snapshots.json"
    snapshots_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Escrito: {snapshots_path} ({len(records)} registros)")

    # ── Alertas reales, no de demostracion ─────────────────────────────────
    alerts: list[dict] = []
    if not args.skip_detectors:
        # Un temporal del sistema, nunca dentro del arbol que se publica:
        # cualquier cosa bajo web/ acaba servida por Pages.
        # English: a system temp dir, never inside the published tree.
        with tempfile.TemporaryDirectory(prefix="vigil-replay-") as tmp:
            alerts = run_detectors(dataset, files, Path(tmp))

    alerts_path = out_dir / "alerts.json"
    alerts_path.write_text(json.dumps(alerts, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Escrito: {alerts_path} ({len(alerts)} alertas)")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset.relative_to(REPO_ROOT)) if dataset.is_relative_to(REPO_ROOT) else str(dataset),
        "files": len(files),
        "merkle_root": computed,
        "merkle_verified": True,
        "ots_proof": f"{dataset.name}/MERKLE_ROOT_HN2025.ots",
        "alerts": len(alerts),
        "note": (
            "Reproduccion local de un conjunto verificado. No es captura en vivo. "
            "El anclaje prueba que estos archivos existian en esta forma en la fecha "
            "del anclaje, no custodia continua durante el conteo."
        ),
    }
    manifest_path = out_dir / "replay_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Escrito: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
