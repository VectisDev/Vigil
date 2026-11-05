"""Pruebas de corrección por comparaciones múltiples.

Tests for multiple-comparisons correction.

El vector de referencia es el ejemplo canónico de Benjamini & Hochberg (1995),
con m=15 y alfa=0.05, donde el procedimiento rechaza exactamente las 4
hipótesis de menor p-valor.

The reference vector is the canonical Benjamini & Hochberg (1995) example, with
m=15 and alpha=0.05, where the procedure rejects exactly the 4 smallest
p-values.
"""

from __future__ import annotations

import pytest

from vigil.core.stats.multiple_testing import benjamini_hochberg, bonferroni

# Ejemplo canónico BH95 / canonical BH95 example.
BH95 = [
    0.0001, 0.0004, 0.0019, 0.0095, 0.0201,
    0.0278, 0.0298, 0.0344, 0.0459, 0.3240,
    0.4262, 0.5719, 0.6528, 0.7590, 1.0000,
]


def test_bh95_rejects_exactly_four():
    reject, qvalues = benjamini_hochberg(BH95, alpha=0.05)
    assert sum(reject) == 4
    assert reject[:4] == [True, True, True, True]
    assert not any(reject[4:])
    assert len(qvalues) == len(BH95)


def test_bh_qvalues_are_monotone_in_pvalue_order():
    _, qvalues = benjamini_hochberg(BH95, alpha=0.05)
    assert qvalues == sorted(qvalues), "q-values must not decrease as p increases"


def test_bh_preserves_input_order():
    shuffled = [BH95[7], BH95[0], BH95[14], BH95[3]]
    reject, qvalues = benjamini_hochberg(shuffled, alpha=0.05)
    # El menor p-valor de la familia está en la posición 1.
    assert qvalues[1] == min(qvalues)
    assert reject[1] is True
    assert reject[2] is False  # p = 1.0


def test_bh_is_never_more_conservative_than_bonferroni():
    _, bh_q = benjamini_hochberg(BH95, alpha=0.05)
    _, bonf = bonferroni(BH95, alpha=0.05)
    assert all(q <= b + 1e-12 for q, b in zip(bh_q, bonf))


def test_bh_single_hypothesis_is_identity():
    reject, qvalues = benjamini_hochberg([0.03], alpha=0.05)
    assert qvalues == [0.03]
    assert reject == [True]


def test_bh_empty_family():
    assert benjamini_hochberg([], alpha=0.05) == ([], [])
    assert bonferroni([], alpha=0.05) == ([], [])


def test_bonferroni_scales_and_clamps():
    reject, adjusted = bonferroni([0.01, 0.5], alpha=0.05)
    assert adjusted == [0.02, 1.0]
    assert reject == [True, False]


@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0])
def test_rejects_out_of_range_pvalues(bad):
    with pytest.raises(ValueError):
        benjamini_hochberg([0.1, bad])
    with pytest.raises(ValueError):
        bonferroni([0.1, bad])


@pytest.mark.parametrize("bad_alpha", [0.0, -0.1, 1.5])
def test_rejects_invalid_alpha(bad_alpha):
    with pytest.raises(ValueError):
        benjamini_hochberg([0.1], alpha=bad_alpha)
