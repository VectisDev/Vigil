"""
======================== ESPAÑOL ========================
Archivo: `src/centinel/core/rules/late_mesa_rule.py`.

Regla de aparición tardía de mesas. Detecta mesas que aparecen por
primera vez con datos cuando el escrutinio ya está muy avanzado, y/o
en lotes grandes. Es el patrón "se dejan para el final": actas
apartadas que entran en bloque cuando hay menos escrutinio público.

Heurística honesta: la severidad es WARNING por defecto y escala a
CRITICAL solo si el lote tardío es grande Y el escrutinio ya estaba
casi cerrado. Degrada con gracia sin snapshot previo, sin mesas, o
si no se puede estimar el porcentaje escrutado.

======================== ENGLISH ========================
Late-appearance rule. Flags tables first seen with data when the
count is already largely closed and/or arriving in large batches
("left for the end" pattern). WARNING by default; CRITICAL only when
a large late batch coincides with a near-closed count. Gracefully
no-ops without a previous snapshot or per-table data.
"""

from __future__ import annotations

from typing import List, Optional

from centinel.core.mesa_forensics import index_mesas
from centinel.core.rules.common import extract_porcentaje_escrutado
from centinel.core.rules.registry import rule


@rule(
    name="Aparición Tardía de Registros en el JSON",
    severity="WARNING",
    description="Registros que el JSON introduce tarde y/o en lotes grandes con el escrutinio casi cerrado.",
    config_key="late_mesa",
)
def apply(current_data: dict, previous_data: Optional[dict], config: dict) -> List[dict]:
    """Detecta mesas nuevas que llegan tarde y/o en lote grande.

    English:
        Detect newly appearing tables arriving late and/or in a large
        batch when the count is already near-closed.
    """
    cfg = config or {}
    near_closed_pct = float(cfg.get("near_closed_pct", 0.90))
    large_batch = int(cfg.get("large_batch", 50))
    max_listed = int(cfg.get("max_listed", 25))

    if not index_mesas(current_data):
        return []
    if not previous_data:
        return []

    previous_index = index_mesas(previous_data)
    current_index = index_mesas(current_data)
    if not current_index:
        return []

    new_codes = sorted(set(current_index) - set(previous_index))
    if not new_codes:
        return []

    pct = extract_porcentaje_escrutado(previous_data)
    if pct is None:
        pct = extract_porcentaje_escrutado(current_data)
    # Normaliza: algunos payloads usan 0-1, otros 0-100.
    if pct is not None and pct > 1.0:
        pct = pct / 100.0

    is_near_closed = pct is not None and pct >= near_closed_pct
    is_large_batch = len(new_codes) >= large_batch

    if not (is_near_closed or is_large_batch):
        return []

    severity = "CRITICAL" if (is_near_closed and is_large_batch) else "WARNING"
    message = (
        f"{len(new_codes)} registro(s) nuevos aparecieron tarde en el JSON "
        f"(escrutado previo ~{round((pct or 0) * 100, 1)}%, "
        f"lote={'grande' if is_large_batch else 'normal'})."
    )
    return [
        {
            "type": "Registros de Aparición Tardía en el JSON",
            "severity": severity,
            "message": message,
            "value": {
                "mesas_nuevas": len(new_codes),
                "porcentaje_escrutado_previo": pct,
                "lote_grande": is_large_batch,
                "escrutinio_casi_cerrado": is_near_closed,
                "codigos": new_codes[:max_listed],
            },
            "threshold": {
                "near_closed_pct": near_closed_pct,
                "large_batch": large_batch,
            },
            "result": (
                severity,
                message,
                {"mesas_nuevas": len(new_codes)},
                {"large_batch": large_batch},
            ),
            "justification": (
                "Centinel audita el JSON publicado, no actas. Que el JSON "
                "introduzca un bloque de registros nuevos cuando el escrutinio "
                "público está casi cerrado es el patrón histórico de "
                "consolidación. Es una observación sobre la secuencia de "
                "publicación (heurística, no prueba), por eso WARNING salvo "
                "lote grande con escrutinio casi cerrado."
            ),
        }
    ]
