"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `src/centinel/core/rules/inconsistency_rate_rule.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - apply

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `src/centinel/core/rules/inconsistency_rate_rule.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - apply

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

# Inconsistency Rate Rule Module
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

from typing import List, Optional

from vigil.core.rules.common import extract_inconsistency_data
from vigil.core.rules.registry import rule


@rule(
    name="Tasa de Actas Inconsistentes",
    severity="CRITICAL",
    description=(
        "Detecta % de actas inconsistentes sobre divulgadas > umbral crítico "
        "o escalada sostenida entre snapshots. "
        "Calibrado con datos reales Honduras 2025 (baseline observado: 14.3%)."
    ),
    config_key="inconsistency_rate",
)
def apply(current_data: dict, previous_data: Optional[dict], config: dict) -> List[dict]:
    """
    Evalúa la tasa de actas inconsistentes respecto al total divulgado.

    Emite alerta CRITICAL cuando:
    - La tasa supera `critical_pct` (nivel absoluto).
    - La tasa aumenta más de `escalation_delta_pct` respecto al snapshot anterior.

    Diseñado a partir del hallazgo forense Honduras 2025: 14.3% de actas marcadas
    como inconsistentes desde el primer snapshot, con escalada final a 14.6% en
    los últimos días. Las 2,773 actas retenidas al 99.4% representaron ~450,000
    votos inauditables.

    Args:
        current_data: Snapshot JSON actual del CNE.
        previous_data: Snapshot JSON anterior (None en el primer snapshot).
        config: Configuración específica de la regla (rules.yaml).

    Returns:
        Lista de alertas en formato estándar.

    English:
        Evaluates the rate of inconsistent tally sheets relative to total disclosed.

        Emits CRITICAL alert when:
        - Rate exceeds `critical_pct` (absolute level).
        - Rate increases more than `escalation_delta_pct` vs. the previous snapshot.

        Designed from the Honduras 2025 forensic finding: 14.3% of tally sheets
        marked as inconsistent from the first snapshot, escalating to 14.6% by
        final days. The 2,773 retained sheets at 99.4% represented ~450,000
        un-auditable votes.

    Args:
        current_data: Current CNE JSON snapshot.
        previous_data: Previous JSON snapshot (None for the first snapshot).
        config: Rule-specific configuration (rules.yaml).

    Returns:
        List of alerts in standard format.
    """
    alerts: List[dict] = []

    current = extract_inconsistency_data(current_data)
    actas_inconsistentes = current["actas_inconsistentes"]
    actas_divulgadas = current["actas_divulgadas"]

    if not actas_divulgadas or actas_inconsistentes is None:
        return alerts

    rate = actas_inconsistentes / actas_divulgadas
    critical_pct = float(config.get("critical_pct", 10)) / 100
    escalation_delta_pct = float(config.get("escalation_delta_pct", 1.0)) / 100

    # ── Alerta de nivel absoluto ──────────────────────────────────────────
    if rate >= critical_pct:
        message = (
            f"Actas inconsistentes={actas_inconsistentes:,} "
            f"({rate:.1%} del total divulgado). "
            f"Umbral crítico: {critical_pct:.0%}."
        )
        alerts.append(
            {
                "type": "Tasa de Actas Inconsistentes — Nivel Crítico",
                "severity": "CRITICAL",
                "message": message,
                "value": {
                    "actas_inconsistentes": actas_inconsistentes,
                    "actas_divulgadas": actas_divulgadas,
                    "rate": rate,
                },
                "threshold": {"critical_pct": critical_pct},
                "result": (
                    "CRITICAL",
                    message,
                    {"rate": rate, "actas_inconsistentes": actas_inconsistentes},
                    {"critical_pct": critical_pct},
                ),
                "justification": (
                    f"La tasa de actas inconsistentes ({rate:.2%}) supera el umbral crítico "
                    f"({critical_pct:.0%}). "
                    f"actas_inconsistentes={actas_inconsistentes:,}, "
                    f"actas_divulgadas={actas_divulgadas:,}."
                ),
            }
        )

    # ── Alerta de escalada entre snapshots ───────────────────────────────
    if previous_data:
        prev = extract_inconsistency_data(previous_data)
        prev_inconsistentes = prev["actas_inconsistentes"]
        prev_divulgadas = prev["actas_divulgadas"]

        if prev_divulgadas and prev_inconsistentes is not None and prev_divulgadas > 0:
            prev_rate = prev_inconsistentes / prev_divulgadas
            delta = rate - prev_rate

            if delta >= escalation_delta_pct:
                message = (
                    f"Escalada de actas inconsistentes: "
                    f"{prev_rate:.2%} → {rate:.2%} "
                    f"(Δ={delta:+.2%}). "
                    f"Umbral de escalada: {escalation_delta_pct:.1%}."
                )
                alerts.append(
                    {
                        "type": "Tasa de Actas Inconsistentes — Escalada",
                        "severity": "CRITICAL",
                        "message": message,
                        "value": {
                            "rate_current": rate,
                            "rate_previous": prev_rate,
                            "delta": delta,
                            "actas_inconsistentes_current": actas_inconsistentes,
                            "actas_inconsistentes_previous": prev_inconsistentes,
                        },
                        "threshold": {"escalation_delta_pct": escalation_delta_pct},
                        "result": (
                            "CRITICAL",
                            message,
                            {"rate_current": rate, "rate_previous": prev_rate, "delta": delta},
                            {"escalation_delta_pct": escalation_delta_pct},
                        ),
                        "justification": (
                            f"La tasa de actas inconsistentes escaló de {prev_rate:.2%} "
                            f"a {rate:.2%} (Δ={delta:+.2%}), "
                            f"superando el umbral de escalada ({escalation_delta_pct:.1%}). "
                            f"Nuevas inconsistencias: "
                            f"{actas_inconsistentes - prev_inconsistentes:+,} actas."
                        ),
                    }
                )

    return alerts
