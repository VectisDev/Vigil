"""
======================== ESPAÑOL ========================
Archivo: `src/centinel/core/rules/mesa_reconciliation_rule.py`.

Centinel audita el JSON publicado por el CNE, no actas. Esta regla
compara el JSON anterior contra el actual, registro por registro
(usando el identificador que el propio JSON trae, p. ej. `codigo_mesa`).
Si un registro que el CNE ya había publicado cambia su huella
criptográfica (su contenido fue modificado en una publicación
posterior), se emite alerta CRITICAL con el delta por candidato y el
candidato beneficiado. Es un hecho verificable sobre el JSON, no un
veredicto electoral. Ataca el patrón histórico del escrutinio especial.

Degrada con gracia: sin publicación previa, o si el JSON solo trae
agregados (sin registros identificables), no emite alertas.

======================== ENGLISH ========================
Centinel audits the CNE-published JSON, not tally sheets. This rule
diffs the previous vs current JSON record-by-record (using the JSON's
own identifier). A record the CNE already published whose fingerprint
changes in a later publication is flagged CRITICAL with per-candidate
delta and beneficiary — a verifiable fact about the JSON, not an
electoral verdict. Gracefully no-ops without a previous publication or
identifiable records.
"""

from __future__ import annotations

from typing import List, Optional

from centinel.core.mesa_forensics import (
    candidate_delta,
    index_mesas,
    primary_beneficiary,
)
from centinel.core.rules.registry import rule


@rule(
    name="Mutación de Registros del JSON entre Publicaciones",
    severity="CRITICAL",
    description="Detecta registros del JSON ya publicados que cambian de valor en una publicación posterior.",
    config_key="mesa_reconciliation",
)
def apply(current_data: dict, previous_data: Optional[dict], config: dict) -> List[dict]:
    """Compara huellas por mesa entre snapshot anterior y actual.

    English:
        Compare per-table fingerprints between previous and current
        snapshots; flag tables whose votes were altered after publication.
    """
    max_listed = int((config or {}).get("max_listed", 25))

    alerts: List[dict] = []
    if not index_mesas(current_data):
        return alerts
    if not previous_data:
        return alerts

    previous_index = index_mesas(previous_data)
    current_index = index_mesas(current_data)
    if not previous_index or not current_index:
        return alerts

    changed: List[dict] = []
    for code, prev in previous_index.items():
        curr = current_index.get(code)
        if curr is None:
            # La desaparición de mesas la cubre mesas_diff_rule; aquí
            # solo interesan las mesas presentes que mutaron.
            continue
        if curr["fingerprint"] == prev["fingerprint"]:
            continue
        delta = candidate_delta(prev["candidate_votes"], curr["candidate_votes"])
        changed.append(
            {
                "codigo_mesa": code,
                "departamento": curr.get("departamento") or prev.get("departamento"),
                "delta_por_candidato": delta,
                "beneficiado": primary_beneficiary(delta),
                "votos_previos": prev["candidate_votes"],
                "votos_actuales": curr["candidate_votes"],
            }
        )

    if not changed:
        return alerts

    changed.sort(
        key=lambda c: max((abs(v) for v in c["delta_por_candidato"].values()), default=0),
        reverse=True,
    )

    message = (
        f"{len(changed)} registro(s) del JSON ya publicados cambiaron de valor "
        "entre publicaciones (posible modificación post-publicación)."
    )
    alerts.append(
        {
            "type": "Registro del JSON Modificado entre Publicaciones",
            "severity": "CRITICAL",
            "message": message,
            "value": {
                "mesas_modificadas": len(changed),
                "detalle": changed[:max_listed],
            },
            "threshold": {"mesas_modificadas": 0},
            "result": (
                "CRITICAL",
                message,
                {"mesas_modificadas": len(changed)},
                {"mesas_modificadas": 0},
            ),
            "justification": (
                "Centinel audita el JSON publicado por el CNE, no actas. Un "
                "registro que el CNE ya había publicado no debe cambiar de valor "
                "en una publicación posterior. El cambio de huella criptográfica "
                "del sub-objeto es un hecho verificable sobre el JSON —no un "
                "veredicto electoral— y es el vector histórico del escrutinio "
                "especial."
            ),
        }
    )
    return alerts
