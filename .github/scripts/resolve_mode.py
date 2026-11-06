#!/usr/bin/env python3
"""
======================== ÍNDICE / INDEX ========================
1. Propósito / Purpose
2. Reglas de transición / Transition rules
3. Salidas / Outputs

======================== ESPAÑOL ========================
Archivo: `.github/scripts/resolve_mode.py`.

Único punto donde se decide qué está haciendo el nodo. Lee `.vigil/mode.yaml`
y resuelve el modo efectivo, que no siempre es el declarado: `LIVE` exige
condiciones adicionales y, si alguna falla, el nodo cae a `ARMED`.

Por qué un solo punto: el marcador anterior (`ELECTION_CLOSED`) se comprobaba
con `if [ -f ... ]` en cuatro workflows distintos. Cuatro copias de una regla
binaria cuyo valor por defecto era seguir capturando contra una fuente muerta.

Fallo cerrado: cualquier ambigüedad resuelve a `ARMED`, que emite cero
peticiones. Un modo que ante la duda raspa una fuente ajena está del revés.

======================== ENGLISH ========================
File: `.github/scripts/resolve_mode.py`.

The single place where the node's state is decided. Reads `.vigil/mode.yaml`
and resolves the effective mode, which is not always the declared one: `LIVE`
requires further conditions and falls back to `ARMED` if any fails.

Why one place: the previous marker (`ELECTION_CLOSED`) was checked with
`if [ -f ... ]` in four separate workflows -- four copies of a binary rule
whose default was to keep collecting against a dead source.

Fail closed: any ambiguity resolves to `ARMED`, which issues zero requests.
A mode that scrapes someone else's server when in doubt is backwards.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

VALID_MODES = ("REPLAY", "ARMED", "LIVE")
DEFAULT_PATH = Path(".vigil/mode.yaml")


def _parse_iso(value: str | None) -> datetime | None:
    """ISO 8601 con `Z` o desplazamiento. / ISO 8601 with `Z` or offset."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def resolve(config: dict, now: datetime | None = None) -> tuple[str, str]:
    """Devuelve `(modo, razón)`. La razón siempre es legible para una persona.

    English: returns `(mode, reason)`. The reason is always human-readable,
    because it is what the public panel shows when there is no data. A state
    the panel cannot explain is indistinguishable from a bug.
    """
    now = now or datetime.now(timezone.utc)
    declared = str(config.get("mode", "REPLAY")).strip().upper()

    # Un problema de entorno (archivo ausente, YAML roto, PyYAML sin instalar)
    # degrada a REPLAY, que es seguro, pero no debe pasar inadvertido: un nodo
    # que deja de capturar por una dependencia rota se ve igual que uno que no
    # tiene nada que capturar.
    # English: an environment problem (missing file, broken YAML, PyYAML not
    # installed) degrades to REPLAY, which is safe, but must not go unnoticed:
    # a node that stops collecting because of a broken dependency looks exactly
    # like one with nothing to collect.
    note = config.get("_note")

    if declared not in VALID_MODES:
        return "ARMED", f"modo declarado invalido ({declared!r}); se asume ARMED"

    if declared == "REPLAY":
        if note:
            return "REPLAY", f"estado no legible, se asume REPLAY: {note}"
        dataset = (config.get("replay") or {}).get("dataset")
        return "REPLAY", f"reproduccion del conjunto verificado {dataset}"

    if declared == "ARMED":
        name = (config.get("election") or {}).get("name") or "sin elección declarada"
        return "ARMED", f"a la espera de eleccion: {name}"

    # A partir de aqui, declared == "LIVE". Cada condicion que falte degrada
    # a ARMED con su motivo, nunca a un LIVE parcial.
    source = config.get("source") or {}
    if not source.get("active"):
        return "ARMED", "source.active es false; la fuente no esta habilitada"

    election = config.get("election") or {}
    start = _parse_iso(election.get("window_start"))
    end = _parse_iso(election.get("window_end"))

    if start is None or end is None:
        return "ARMED", "ventana electoral sin fechas; no se puede abrir LIVE"
    if now < start:
        return "ARMED", f"la ventana electoral abre el {start.isoformat()}"
    if now > end:
        return "ARMED", f"la ventana electoral cerro el {end.isoformat()}"

    return "LIVE", f"ventana abierta hasta {end.isoformat()}"


def load_config(path: Path) -> dict:
    """Carga el estado declarado. Ausencia o error resuelven a REPLAY.

    English: load the declared state. A missing or unreadable file resolves to
    REPLAY, the zero-request mode -- never to one that contacts a source.
    """
    if not path.exists():
        return {"mode": "REPLAY", "_note": f"{path} no existe"}
    try:
        import yaml  # dependencia de produccion ya presente / already a prod dep

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"mode": "REPLAY"}
    except Exception as exc:  # noqa: BLE001
        # Un archivo de estado ilegible no debe habilitar la captura.
        # An unreadable state file must never enable collection.
        return {"mode": "REPLAY", "_note": f"{path} ilegible: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Resuelve el modo efectivo del nodo.")
    parser.add_argument("--path", default=str(DEFAULT_PATH))
    parser.add_argument("--json", action="store_true", help="Emite JSON por stdout.")
    args = parser.parse_args()

    config = load_config(Path(args.path))
    mode, reason = resolve(config)

    # `go` es lo que consulta el gate de captura: solo LIVE captura.
    # `go` is what the capture gate reads: only LIVE collects.
    go = "true" if mode == "LIVE" else "false"

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(f"mode={mode}\n")
            fh.write(f"reason={reason}\n")
            fh.write(f"go={go}\n")

    if args.json:
        print(json.dumps({"mode": mode, "reason": reason, "go": go == "true"}))
    else:
        print(f"mode={mode} go={go} reason={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
