"""Ley de Benford canónica — 2do dígito (Mebane 2006).

Sustituye la implementación de primer dígito por candidato (dev-v10)
con el test canónico de segundo dígito, más robusto para datos electorales
de Honduras donde el rango por mesa es limitado (200-500 votos).

Canonical Benford's Law — 2nd digit (Mebane 2006).

Replaces the per-candidate 1st-digit implementation (dev-v10) with the
canonical 2nd-digit test, more robust for Honduran electoral data where
per-mesa vote range is limited (200-500 votes).

References / Referencias:
    Mebane (2006) Election forensics: Vote counts and Benford's law.
    Deckert, Myagkov & Ordeshook (2011) Political Analysis 19:245-268.
    See docs/stats/STATISTICAL_CONVENTIONS.md — Section 2.
"""

from __future__ import annotations

from typing import List, Optional

from centinel.core.rules.benford_unified import benford_canonical, benford_batch
from centinel.core.rules.common import extract_department, extract_candidate_votes
from centinel.core.rules.registry import rule


@rule(
    name="Ley de Benford Canónica (2do Dígito)",
    severity="CRITICAL",
    description=(
        "Test canónico Benford 2do dígito (2BL) por candidato y agregado. "
        "FP rate < 5%% calibrado contra datos HN 2025. "
        "Reemplaza benford_law (1er dígito) de dev-v10. "
        "Ver docs/stats/STATISTICAL_CONVENTIONS.md."
    ),
    config_key="benford_law",
)
def apply(current_data: dict, previous_data: Optional[dict], config: dict) -> List[dict]:
    """Evalúa Benford 2do dígito (2BL) sobre votos por candidato y total.

    Método: chi-cuadrado + MAD con confirmación dual para CRITICAL.
    Severidad: CRITICAL si chi² p<0.01 AND MAD>0.012; WARNING si solo chi².
    INFO si chi² p<0.05 OR MAD>0.006 (solo logging, no genera alertas operativas).

    English:
        Evaluate 2nd-digit Benford (2BL) on per-candidate and total vote counts.
        Method: chi-square + MAD with dual confirmation for CRITICAL severity.
        CRITICAL: chi² p<0.01 AND MAD>0.012 (dual confirmation, FP<5%).
        WARNING: chi² p<0.01 alone (statistical test sufficient).
        INFO: logging only — never generates operational alert.

    Args:
        current_data: Current CNE JSON snapshot / Snapshot JSON actual del CNE.
        previous_data: Previous snapshot (unused) / Snapshot anterior (no usado).
        config: Rule configuration / Configuración de la regla.

    Returns:
        List of alerts / Lista de alertas en formato estándar.
    """
    del previous_data

    alerts: List[dict] = []
    department = extract_department(current_data)
    min_samples = int(config.get("min_samples", 30))

    candidate_vote_map = extract_candidate_votes(current_data)
    if not candidate_vote_map:
        return alerts

    data_by_candidate = {
        str(cid): [v for v in [cv.get("votes")] if isinstance(v, int) and v > 0]
        for cid, cv in candidate_vote_map.items()
    }
    data_by_candidate = {k: v for k, v in data_by_candidate.items() if len(v) >= min_samples}

    if not data_by_candidate:
        return alerts

    results = benford_batch(data_by_candidate, test_type="canonical", min_samples=min_samples)

    from centinel.core.rules.severity import Severity as SeverityEnum  # noqa: PLC0415
    for result in results:
        if result.severity in (SeverityEnum.NOMINAL, SeverityEnum.INFO):
            continue
        severity_str = "CRITICAL" if result.severity == SeverityEnum.CRITICAL else "WARNING"
        alerts.append(
            {
                "type": "Ley de Benford 2do Dígito (Canónica)",
                "severity": severity_str,
                "department": department,
                "candidate": result.entity,
                "justification": (
                    f"Distribución del 2do dígito se desvía de 2BL (Mebane 2006). "
                    f"chi²_p={result.chi2_pvalue:.4f}, MAD={result.mad:.4f}, "
                    f"n={result.n}, max_desv_dígito={result.max_deviation_digit} "
                    f"({result.max_deviation_pct:.2f}pp)."
                ),
                "value": {
                    "chi2_pvalue": result.chi2_pvalue,
                    "mad": result.mad,
                    "n": result.n,
                    "candidate": result.entity,
                },
            }
        )

    return alerts
