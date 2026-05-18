"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `src/centinel/core/rules/benford_first_digit_rule.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - _first_digit
  - _collect_votes_by_candidate
  - apply              (config_key: benford_first_digit — MAD + chi-cuadrado agregado)
  - apply_per_candidate (config_key: benford_law — chi-cuadrado por candidato)

Notas:
- Módulo canónico de Benford. Contiene ambas variantes para evitar duplicación.
  benford_law_rule.py es un stub vacío mantenido por compatibilidad de importación.
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.

======================== ENGLISH ========================
File: `src/centinel/core/rules/benford_first_digit_rule.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - _first_digit
  - _collect_votes_by_candidate
  - apply               (config_key: benford_first_digit — MAD + chi-square aggregate)
  - apply_per_candidate  (config_key: benford_law — chi-square per candidate)

Notes:
- Canonical Benford module. Both variants live here to avoid duplication.
  benford_law_rule.py is an empty stub kept for import compatibility.
- Keep this header in sync with structural changes in the file.
"""

# Benford Rules Module (canonical)
# AUTO-DOC-INDEX
#
# ES: Índice rápido
#   1) Propósito del módulo
#   2) Componentes principales
#   3) Puntos de extensión
#
# EN: Quick index
#   1) Module purpose
#   2) Main components
#   3) Extension points
#
# Secciones / Sections:
#   - Configuración / Configuration
#   - Lógica principal / Core logic
#   - Integraciones / Integrations


from __future__ import annotations

import collections
import math
from typing import Dict, List, Optional

import numpy as np
from scipy.stats import chisquare

from centinel.core.rules.common import (
    extract_candidate_votes,
    extract_department,
    extract_numeric_list,
    extract_total_votes,
    safe_int_or_none,
)
from centinel.core.rules.registry import rule

# ── Shared helpers ────────────────────────────────────────────────────────


def _first_digit(number: int) -> Optional[int]:
    """Extrae el primer dígito de un entero positivo; None si ≤ 0."""
    if number <= 0:
        return None
    return int(str(number)[0])


def _collect_votes_by_candidate(data: dict) -> Dict[str, List[int]]:
    """Agrupa votos positivos por candidato desde estructuras heterogéneas del CNE.

    Inspecciona listas de candidatos y mesas, filtrando votos inválidos o negativos.

    English:
        Group positive votes per candidate from heterogeneous CNE structures.
    """
    votes_by_candidate: Dict[str, List[int]] = collections.defaultdict(list)

    def _append(entries: object) -> None:
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            cid = str(
                entry.get("id")
                or entry.get("candidate_id")
                or entry.get("nombre")
                or entry.get("name")
                or entry.get("candidato")
                or "unknown"
            )
            votes = safe_int_or_none(entry.get("votos") or entry.get("votes"))
            if votes is None or votes <= 0:
                continue
            votes_by_candidate[cid].append(votes)

    _append(data.get("votos") or data.get("candidates") or data.get("candidatos"))
    mesas = data.get("mesas") or data.get("tables") or []
    if isinstance(mesas, list):
        for mesa in mesas:
            if isinstance(mesa, dict):
                _append(mesa.get("votos") or mesa.get("candidates") or [])
    return votes_by_candidate


# ── Rule 1: Benford primer dígito — MAD + chi-cuadrado agregado ───────────


@rule(
    name="Ley de Benford (Primer Dígito)",
    severity="CRITICAL",
    description="Evalúa MAD y chi-cuadrado sobre distribución del primer dígito (vista agregada).",
    config_key="benford_first_digit",
)
def apply(current_data: dict, previous_data: Optional[dict], config: dict) -> List[dict]:
    """Evalúa la Ley de Benford sobre el primer dígito de los votos totales por candidato.

    Método: MAD (mean absolute deviation) + chi-cuadrado sobre la distribución
    agregada de todos los candidatos y el total emitido.

    English:
        Evaluate Benford's Law on first digits of aggregate candidate vote totals.
        Method: MAD + chi-square on combined candidate + total-vote distribution.
    """
    del previous_data

    alerts: List[dict] = []
    department = extract_department(current_data)
    candidate_votes = extract_numeric_list(
        candidate.get("votes") for candidate in extract_candidate_votes(current_data).values()
    )
    total_votes = extract_total_votes(current_data)
    if total_votes is not None:
        candidate_votes.append(total_votes)

    min_samples = int(config.get("min_samples", 15))
    if len(candidate_votes) < min_samples:
        return alerts

    digits = [d for d in (_first_digit(v) for v in candidate_votes) if d]
    if len(digits) < min_samples:
        return alerts

    observed_counts = np.array([digits.count(d) for d in range(1, 10)], dtype=float)
    total = observed_counts.sum()
    if total == 0:
        return alerts

    expected_probs = np.array([math.log10(1 + 1 / d) for d in range(1, 10)])
    expected_counts = expected_probs * total
    mad = float(np.mean(np.abs((observed_counts / total) - expected_probs)))
    chi_result = chisquare(observed_counts, f_exp=expected_counts)

    mad_warning = float(config.get("mad_warning", 0.008))
    mad_critical = float(config.get("mad_critical", 0.015))
    chi_pvalue_critical = float(config.get("chi_pvalue_critical", 0.01))

    if mad > mad_critical or chi_result.pvalue < chi_pvalue_critical:
        severity = "CRITICAL"
    elif mad_warning <= mad <= mad_critical:
        severity = "WARNING"
    else:
        return alerts

    message = (
        f"La distribución del primer dígito se desvía de Benford con MAD "
        f"{mad:.4f} y p-value {chi_result.pvalue:.4f}."
    )
    alerts.append(
        {
            "type": "Ley de Benford Primer Dígito",
            "severity": severity,
            "department": department,
            "message": message,
            "value": {
                "mad": mad,
                "p_value": float(chi_result.pvalue),
                "observed_pct": (observed_counts / total * 100).tolist(),
                "expected_pct": (expected_probs * 100).tolist(),
            },
            "threshold": {
                "mad_warning": mad_warning,
                "mad_critical": mad_critical,
                "chi_pvalue_critical": chi_pvalue_critical,
            },
            "result": (
                severity,
                message,
                {"mad": mad, "p_value": float(chi_result.pvalue)},
                {"mad_warning": mad_warning, "mad_critical": mad_critical, "chi_pvalue_critical": chi_pvalue_critical},
            ),
            "justification": (
                f"Benford 1BL agregado: muestras={len(digits)}, " f"MAD={mad:.4f}, pvalue_chi2={chi_result.pvalue:.4f}."
            ),
        }
    )
    return alerts


# ── Rule 2: Benford por candidato — chi-cuadrado individual ──────────────
# Consolidado desde benford_law_rule.py (investigación; deshabilitado por defecto).


@rule(
    name="Ley de Benford (por Candidato)",
    severity="Medium",
    description="Chi-cuadrado del primer dígito por candidato individual (regla de investigación).",
    config_key="benford_law",
)
def apply_per_candidate(current_data: dict, previous_data: Optional[dict], config: dict) -> List[dict]:
    """Evalúa Benford por candidato usando chi-cuadrado sobre series individuales de mesas.

    Complementa `benford_first_digit` con visibilidad por candidato. Es una regla
    de investigación (deshabilitada por defecto); se activa con
    `rules.enable_research_rules: true` en rules.yaml.

    English:
        Evaluate Benford per candidate using chi-square on individual mesa series.
        Complements `benford_first_digit` with per-candidate visibility.
        Research rule — disabled by default.
    """
    del previous_data

    alerts: List[dict] = []
    votes_by_candidate = _collect_votes_by_candidate(current_data)
    if not votes_by_candidate:
        return alerts

    min_samples = int(config.get("min_samples", 10))
    deviation_threshold = float(config.get("deviation_pct", 15))
    chi_square_threshold = float(config.get("chi_square_threshold", 0.05))

    expected_pct = {d: math.log10(1 + 1 / d) * 100 for d in range(1, 10)}
    department = extract_department(current_data)

    for candidate, votes in votes_by_candidate.items():
        if len(votes) < min_samples:
            continue
        first_digits = [int(str(v)[0]) for v in votes if v and str(v)[0].isdigit()]
        if len(first_digits) < min_samples:
            continue

        counts = collections.Counter(first_digits)
        observed = [counts.get(d, 0) for d in range(1, 10)]
        total = sum(observed)
        if total <= 0:
            continue

        expected = [expected_pct[d] / 100 * total for d in range(1, 10)]
        chi_result = chisquare(observed, f_exp=expected)
        obs_pct = {d: (counts.get(d, 0) / total) * 100 for d in range(1, 10)}
        deviation_pct = max(abs(obs_pct[d] - expected_pct[d]) for d in range(1, 10))

        if chi_result.pvalue >= chi_square_threshold and deviation_pct < deviation_threshold:
            continue

        alerts.append(
            {
                "type": "Desviación Ley de Benford",
                "severity": "Medium",
                "department": department,
                "justification": (
                    f"Benford por candidato: candidato={candidate}, muestras={total}, "
                    f"chi2={chi_result.statistic:.2f}, pvalue={chi_result.pvalue:.4f}, "
                    f"desviación_max={deviation_pct:.2f}% (umbral={deviation_threshold:.2f}%)."
                ),
            }
        )

    return alerts
