"""El veredicto nombra el criterio que lo disparó, y corrige la familia.

The verdict names the criterion that fired, and corrects the family.

Estas pruebas nacen de una salida concreta del replay forense sobre el conjunto
real de Honduras 2025:

    Progressive injection: DETECTED
      Z-score: -1.661 (p=0.09671)

Un lector veía «DETECTED» junto a un p no significativo y un z de signo
contrario al de la hipótesis, y concluía —con razón— que el proyecto declaraba
detecciones sobre resultados no significativos. Lo que ocurría era distinto y
peor de explicar: había disparado OTRO criterio, y el estadístico mostrado no
era el que había disparado.

A reader saw "DETECTED" next to a non-significant p and a z pointing the
opposite way to the hypothesis, and concluded -- reasonably -- that the project
declares detections on non-significant results. What actually happened was
different and harder to explain: a DIFFERENT criterion had fired, and the
statistic on display was not the one that fired.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from auditor.inconsistent_acts import InconsistentActsTracker  # noqa: E402


@pytest.fixture
def tracker() -> InconsistentActsTracker:
    return InconsistentActsTracker()


# ── la familia de p-valores se corrige ────────────────────────────────────────


def test_pvalue_family_is_corrected(tracker: InconsistentActsTracker):
    stats = tracker.run_injection_statistical_tests([10.0, 12.0, 9.0, 11.0, 10.5])
    mt = stats["multiple_testing"]
    assert mt["method"] == "bh"
    assert mt["family_size"] == 2
    assert set(mt["tests"]) == {"z_cumulative", "runs"}
    assert set(mt["bh_qvalues"]) == {"z_cumulative", "runs"}


def test_qvalue_is_never_below_its_raw_pvalue(tracker: InconsistentActsTracker):
    """Corregir solo puede hacer el veredicto más exigente, nunca menos."""
    stats = tracker.run_injection_statistical_tests([3.0, 1.0, 4.0, 1.0, 5.0, 9.0])
    mt = stats["multiple_testing"]
    for name in mt["tests"]:
        assert mt["bh_qvalues"][name] >= mt["raw_pvalues"][name] - 1e-12


def test_significance_is_decided_on_the_corrected_value(tracker: InconsistentActsTracker):
    """Ninguna prueba se declara significativa con q por encima de alfa."""
    stats = tracker.run_injection_statistical_tests([2.0, 7.0, 1.0, 8.0, 2.0, 8.0])
    mt = stats["multiple_testing"]
    alpha = mt["alpha"]
    for name in stats["significant_after_correction"]:
        assert mt["bh_qvalues"][name] <= alpha


# ── heurísticas y pruebas con p-valor no se mezclan ───────────────────────────


def test_heuristics_are_reported_apart_from_pvalue_tests(tracker: InconsistentActsTracker):
    """Varianza nula y autocorrelación no tienen p-valor: no son pruebas.

    English: near-zero variance and autocorrelation have no p-value; they are
    not tests. Folding them into the same disjunction as the p-values is what
    made the output unreadable.
    """
    # Seis deltas idénticos: varianza cero, el caso del conjunto real de 2025.
    stats = tracker.run_injection_statistical_tests([0.0] * 6)
    assert "near_zero_variance" in stats["heuristics_fired"]
    assert "near_zero_variance" not in stats["significant_after_correction"]
    assert set(stats["significant_after_correction"]).issubset({"z_cumulative", "runs"})


def test_triggered_by_is_the_union_and_is_never_empty_when_improbable(
    tracker: InconsistentActsTracker,
):
    stats = tracker.run_injection_statistical_tests([0.0] * 6)
    assert stats["improbable"] is True
    assert stats["triggered_by"]
    assert stats["triggered_by"] == (stats["significant_after_correction"] + stats["heuristics_fired"])


def test_nothing_fires_on_plainly_random_deltas(tracker: InconsistentActsTracker):
    """Sin señal, no hay veredicto ni criterio disparado."""
    stats = tracker.run_injection_statistical_tests([120.0, 45.0, 230.0, 80.0, 310.0, 60.0])
    assert stats["improbable"] is bool(stats["triggered_by"])
    if not stats["triggered_by"]:
        assert stats["significant_after_correction"] == []
        assert stats["heuristics_fired"] == []


# ── el caso real que motivó todo esto ─────────────────────────────────────────


def test_the_2025_case_reports_a_heuristic_and_not_a_significant_pvalue(
    tracker: InconsistentActsTracker,
):
    """Reproduce la forma de la salida que un evaluador vio.

    Seis ciclos de delta cero: dispara `near_zero_variance`, y NINGUNA prueba
    con p-valor resulta significativa. El veredicto debe decir exactamente eso.

    English: six zero-delta cycles: `near_zero_variance` fires and NO p-value
    test is significant. The verdict must say exactly that.
    """
    stats = tracker.run_injection_statistical_tests([0.0] * 6)
    assert stats["triggered_by"] == ["near_zero_variance"]
    assert stats["significant_after_correction"] == []
    # El z sigue reportándose, pero ya no como si fuera la evidencia.
    assert "z_score_pvalue" in stats
    assert stats["multiple_testing"]["bh_qvalues"]["z_cumulative"] >= stats["z_score_pvalue"]
