"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `tests/test_inconsistency_rate_rule.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - test_no_alert_below_threshold
  - test_critical_level_alert
  - test_escalation_alert
  - test_no_alert_without_inconsistency_data
  - test_no_previous_data
  - test_canonical_format
  - test_rule_registered

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `tests/test_inconsistency_rate_rule.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - test_no_alert_below_threshold
  - test_critical_level_alert
  - test_escalation_alert
  - test_no_alert_without_inconsistency_data
  - test_no_previous_data
  - test_canonical_format
  - test_rule_registered

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

from __future__ import annotations

import pytest

from vigil.core.rules import inconsistency_rate_rule  # noqa: F401 — auto-registro
from vigil.core.rules.inconsistency_rate_rule import apply
from vigil.core.rules.registry import list_rules


# ── Fixtures ──────────────────────────────────────────────────────────────


def _cne_snap(actas_inconsistentes: int, actas_correctas: int) -> dict:
    """Construye un snapshot en formato JSON crudo del CNE."""
    divulgadas = actas_inconsistentes + actas_correctas
    return {
        "estadisticas": {
            "totalizacion_actas": {
                "actas_totales": "19,152",
                "actas_divulgadas": str(divulgadas),
            },
            "distribucion_votos": {
                "validos": "2,500,000",
                "nulos": "90,000",
                "blancos": "45,000",
            },
            "estado_actas_divulgadas": {
                "actas_correctas": str(actas_correctas),
                "actas_inconsistentes": str(actas_inconsistentes),
            },
        },
        "resultados": [
            {"partido": "PARTIDO A", "candidato": "CANDIDATO X", "votos": "1,200,000", "porcentaje": "48.0"},
            {"partido": "PARTIDO B", "candidato": "CANDIDATO Y", "votos": "1,050,000", "porcentaje": "42.0"},
        ],
    }


def _canonical_snap(actas_inconsistentes: int, actas_divulgadas: int) -> dict:
    """Construye un snapshot en formato canónico de Centinel."""
    return {
        "actas_inconsistentes": actas_inconsistentes,
        "actas_divulgadas": actas_divulgadas,
        "totals": {
            "total_votes": 2500000,
            "valid_votes": 2400000,
            "null_votes": 90000,
            "blank_votes": 45000,
        },
    }


CONFIG_DEFAULT = {"critical_pct": 10, "escalation_delta_pct": 1.0}


# ── Tests de nivel absoluto ───────────────────────────────────────────────


def test_no_alert_below_threshold():
    """No debe alertar cuando la tasa es menor al umbral crítico."""
    snap = _cne_snap(actas_inconsistentes=500, actas_correctas=9500)  # 5%
    alerts = apply(snap, None, CONFIG_DEFAULT)
    assert alerts == []


def test_critical_level_alert():
    """Debe emitir alerta CRITICAL cuando la tasa supera el umbral."""
    # 2189 / 15310 ≈ 14.3% — dato real Honduras 2025 primer snapshot
    snap = _cne_snap(actas_inconsistentes=2189, actas_correctas=13121)
    alerts = apply(snap, None, CONFIG_DEFAULT)
    level_alerts = [a for a in alerts if "Nivel Crítico" in a["type"]]
    assert len(level_alerts) == 1
    a = level_alerts[0]
    assert a["severity"] == "CRITICAL"
    assert a["value"]["actas_inconsistentes"] == 2189
    assert a["value"]["rate"] == pytest.approx(2189 / 15310, rel=1e-3)


def test_at_exact_threshold_triggers():
    """La tasa exactamente igual al umbral debe disparar la alerta."""
    # 10% exacto: 1000 / 10000
    snap = _cne_snap(actas_inconsistentes=1000, actas_correctas=9000)
    alerts = apply(snap, None, CONFIG_DEFAULT)
    level_alerts = [a for a in alerts if "Nivel Crítico" in a["type"]]
    assert len(level_alerts) == 1


# ── Tests de escalada ─────────────────────────────────────────────────────


def test_escalation_alert():
    """Debe emitir alerta de escalada cuando la tasa sube > delta umbral."""
    # prev: 5% → current: 7% (Δ = 2% > 1% umbral)
    prev = _cne_snap(actas_inconsistentes=500, actas_correctas=9500)  # 5%
    curr = _cne_snap(actas_inconsistentes=700, actas_correctas=9300)  # 7%
    alerts = apply(curr, prev, CONFIG_DEFAULT)
    esc_alerts = [a for a in alerts if "Escalada" in a["type"]]
    assert len(esc_alerts) == 1
    a = esc_alerts[0]
    assert a["severity"] == "CRITICAL"
    assert a["value"]["delta"] == pytest.approx(0.02, abs=1e-4)


def test_no_escalation_below_delta():
    """No debe alertar por escalada si el delta está por debajo del umbral."""
    # prev: 14.3% → current: 14.4% (Δ ≈ 0.1% < 1%)
    prev = _cne_snap(actas_inconsistentes=2189, actas_correctas=13121)  # 14.3%
    curr = _cne_snap(actas_inconsistentes=2207, actas_correctas=13125)  # ~14.4%
    alerts = apply(curr, prev, CONFIG_DEFAULT)
    esc_alerts = [a for a in alerts if "Escalada" in a["type"]]
    assert esc_alerts == []


def test_no_previous_data_only_level():
    """Sin snapshot anterior solo aplica la regla de nivel absoluto."""
    snap = _cne_snap(actas_inconsistentes=2000, actas_correctas=8000)  # 20%
    alerts = apply(snap, None, CONFIG_DEFAULT)
    assert all("Nivel Crítico" in a["type"] for a in alerts)
    assert not any("Escalada" in a["type"] for a in alerts)


# ── Tests de datos vacíos o faltantes ────────────────────────────────────


def test_no_alert_without_inconsistency_data():
    """No debe alertar si no hay datos de inconsistencias."""
    snap = {"totals": {"total_votes": 1000000}}
    alerts = apply(snap, None, CONFIG_DEFAULT)
    assert alerts == []


def test_no_alert_zero_actas_divulgadas():
    """No debe alertar si actas_divulgadas es cero (evitar división por cero)."""
    snap = {
        "estadisticas": {
            "estado_actas_divulgadas": {
                "actas_correctas": "0",
                "actas_inconsistentes": "0",
            },
            "totalizacion_actas": {"actas_totales": "19152", "actas_divulgadas": "0"},
        }
    }
    alerts = apply(snap, None, CONFIG_DEFAULT)
    assert alerts == []


# ── Test de formato canónico ──────────────────────────────────────────────


def test_canonical_format():
    """La regla debe funcionar con el formato canónico de Centinel."""
    snap = _canonical_snap(actas_inconsistentes=1500, actas_divulgadas=10000)  # 15%
    alerts = apply(snap, None, CONFIG_DEFAULT)
    level_alerts = [a for a in alerts if "Nivel Crítico" in a["type"]]
    assert len(level_alerts) == 1
    assert level_alerts[0]["value"]["rate"] == pytest.approx(0.15, rel=1e-3)


# ── Test de registro ──────────────────────────────────────────────────────


def test_rule_registered():
    """La regla debe estar registrada en el registry con los metadatos correctos."""
    rules = [r for r in list_rules() if r.config_key == "inconsistency_rate"]
    assert len(rules) == 1
    r = rules[0]
    assert r.name == "Tasa de Actas Inconsistentes"
    assert r.severity == "CRITICAL"
