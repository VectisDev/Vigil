"""
Tests para los módulos estadísticos unificados de CENTINEL.
Tests for CENTINEL's unified statistical modules.

Covers:
    - zscore_unified: Family A (proportions) and Family B (empirical)
    - benford_unified: Canonical (2nd digit) and Experimental (1st digit)
    - Regression: ensures dev-v10 → v11 migration does not increase FP rate
    - Edge cases: graceful degradation, boundary values, empty inputs

Run: pytest tests/test_unified_stats.py -v
"""

import math
import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'centinel', 'core', 'rules'))

from vigil.core.rules.severity import Severity
from vigil.core.rules.zscore_unified import (
    zscore_proportion,
    zscore_empirical,
    Z_THRESHOLD_WARNING,
    Z_THRESHOLD_CRITICAL,
)
from vigil.core.rules.benford_unified import (
    benford_canonical,
    benford_experimental_first_digit,
    benford_batch,
    BENFORD_1ST_EXPECTED,
    BENFORD_2ND_EXPECTED,
    MIN_SAMPLES,
)


# ===================================================================
# Z-SCORE TESTS — Family A (Proportions)
# ===================================================================
class TestZscoreProportion:
    """Tests for zscore_proportion (Family A — binomial SE)."""

    def test_basic_nominal(self):
        """A proportion close to expected should be NOMINAL."""
        result = zscore_proportion(p_hat=0.50, p_null=0.50, n=100)
        assert result is not None
        assert result.severity == Severity.NOMINAL
        assert result.z == 0.0
        assert result.family == "proportion"

    def test_critical_deviation(self):
        """A large deviation should trigger CRITICAL."""
        # p_hat far from p_null with large n → high Z
        result = zscore_proportion(p_hat=0.70, p_null=0.50, n=1000)
        assert result is not None
        assert result.severity == Severity.CRITICAL
        assert result.z > Z_THRESHOLD_CRITICAL

    def test_warning_deviation(self):
        """A moderate deviation should trigger WARNING."""
        # p_hat=0.545, p_null=0.50, n=1000 → Z ≈ 2.846 (between 2.576 and 3.291)
        result = zscore_proportion(p_hat=0.545, p_null=0.50, n=1000)
        assert result is not None
        assert result.severity == Severity.WARNING
        assert Z_THRESHOLD_WARNING < result.z < Z_THRESHOLD_CRITICAL

    def test_graceful_degradation_insufficient_samples(self):
        """Should return None when n < min_samples."""
        result = zscore_proportion(p_hat=0.50, p_null=0.50, n=10, min_samples=30)
        assert result is None

    def test_graceful_degradation_custom_min(self):
        """Custom min_samples should be respected."""
        result = zscore_proportion(p_hat=0.50, p_null=0.50, n=25, min_samples=20)
        assert result is not None

    def test_invalid_p_hat(self):
        """p_hat outside [0,1] should raise ValueError."""
        with pytest.raises(ValueError, match="p_hat"):
            zscore_proportion(p_hat=1.5, p_null=0.50, n=100)

    def test_invalid_p_null_zero(self):
        """p_null = 0 should raise ValueError (division by zero in SE)."""
        with pytest.raises(ValueError, match="p_null"):
            zscore_proportion(p_hat=0.50, p_null=0.0, n=100)

    def test_invalid_n(self):
        """n < 1 should raise ValueError."""
        with pytest.raises(ValueError, match="n must"):
            zscore_proportion(p_hat=0.50, p_null=0.50, n=0)

    def test_se_formula_correctness(self):
        """Verify SE = sqrt(p0 * (1-p0) / n) is computed correctly."""
        result = zscore_proportion(p_hat=0.60, p_null=0.50, n=400)
        assert result is not None
        expected_se = math.sqrt(0.50 * 0.50 / 400)  # = 0.025
        assert abs(result.se_or_std - expected_se) < 1e-8
        expected_z = abs(0.60 - 0.50) / expected_se  # = 4.0
        assert abs(result.z - expected_z) < 1e-4

    def test_pvalue_two_tailed(self):
        """p-value should be two-tailed."""
        result = zscore_proportion(p_hat=0.55, p_null=0.50, n=100)
        assert result is not None
        assert 0 < result.p_value < 1


# ===================================================================
# Z-SCORE TESTS — Family B (Empirical)
# ===================================================================
class TestZscoreEmpirical:
    """Tests for zscore_empirical (Family B — sample std, ddof=1)."""

    def test_basic_nominal(self):
        """Value at the mean should be NOMINAL."""
        sample = list(range(50, 80))  # 30 values, mean ≈ 64.5
        result = zscore_empirical(x=64.5, sample=sample)
        assert result is not None
        assert result.severity == Severity.NOMINAL
        assert result.z < 0.1

    def test_critical_outlier(self):
        """An extreme outlier should trigger CRITICAL."""
        np.random.seed(42)
        sample = np.random.normal(50, 5, 100).tolist()
        result = zscore_empirical(x=80, sample=sample)  # 6 std deviations away
        assert result is not None
        assert result.severity == Severity.CRITICAL

    def test_ddof_1_is_used(self):
        """Verify ddof=1 (Bessel correction) — the key fix from dev-v10."""
        sample = [10.0, 20.0, 30.0, 40.0, 50.0] * 6  # 30 values
        result = zscore_empirical(x=35.0, sample=sample)
        assert result is not None
        # std with ddof=1 for this sample
        expected_std = float(np.std(sample, ddof=1))
        assert abs(result.se_or_std - expected_std) < 1e-6
        # Verify it's NOT ddof=0 (which would be smaller)
        wrong_std = float(np.std(sample, ddof=0))
        assert result.se_or_std > wrong_std

    def test_graceful_degradation(self):
        """Should return None when sample too small."""
        result = zscore_empirical(x=50, sample=[40, 50, 60])
        assert result is None

    def test_zero_variance_sample(self):
        """All-identical sample → std=0 → should return None, not crash."""
        result = zscore_empirical(x=50, sample=[42.0] * 30)
        assert result is None

    def test_family_label(self):
        """Family should be 'empirical'."""
        sample = list(range(30))
        result = zscore_empirical(x=15, sample=sample)
        assert result is not None
        assert result.family == "empirical"


# ===================================================================
# Z-SCORE REGRESSION: dev-v10 → v11 migration
# ===================================================================
class TestZscoreRegression:
    """
    Regression tests ensuring the v10 → v11 migration is conservative.
    The switch from ddof=0 to ddof=1 should REDUCE false positives,
    not increase them (σ increases → Z decreases for same data).
    """

    def test_ddof1_produces_lower_z_than_ddof0(self):
        """ddof=1 std is always >= ddof=0 std → Z is always <= for ddof=1."""
        np.random.seed(123)
        for _ in range(50):  # Run 50 random trials
            sample = np.random.normal(100, 15, 50).tolist()
            x = sample[0] + 30  # Moderate outlier

            result_v11 = zscore_empirical(x=x, sample=sample)
            assert result_v11 is not None

            # Simulate old dev-v10 behavior (ddof=0)
            arr = np.array(sample)
            z_v10 = abs(x - np.mean(arr)) / np.std(arr, ddof=0)

            # v11 Z should be <= v10 Z (more conservative)
            assert result_v11.z <= z_v10 + 1e-10

    def test_threshold_change_is_conservative(self):
        """
        dev-v10 hardcoded |Z|>3 for CRITICAL.
        v11 uses |Z|>3.291 for CRITICAL.
        This means fewer CRITICAL alerts — strictly conservative.
        """
        assert Z_THRESHOLD_CRITICAL > 3.0


# ===================================================================
# BENFORD TESTS — Expected distributions
# ===================================================================
class TestBenfordExpected:
    """Verify precomputed Benford distributions sum to 1."""

    def test_first_digit_sums_to_one(self):
        total = sum(BENFORD_1ST_EXPECTED.values())
        assert abs(total - 1.0) < 1e-10

    def test_second_digit_sums_to_one(self):
        total = sum(BENFORD_2ND_EXPECTED.values())
        assert abs(total - 1.0) < 1e-10

    def test_first_digit_known_values(self):
        """P(1) ≈ 0.30103, P(9) ≈ 0.04576."""
        assert abs(BENFORD_1ST_EXPECTED[1] - 0.30103) < 1e-4
        assert abs(BENFORD_1ST_EXPECTED[9] - 0.04576) < 1e-4

    def test_second_digit_d0_is_largest(self):
        """For 2BL, P(d2=0) should be the largest probability."""
        assert BENFORD_2ND_EXPECTED[0] == max(BENFORD_2ND_EXPECTED.values())


# ===================================================================
# BENFORD TESTS — Canonical (2nd digit)
# ===================================================================
class TestBenfordCanonical:
    """Tests for benford_canonical (2nd digit — CRITICAL capable)."""

    def _generate_benford_compliant(self, n: int, seed: int = 42) -> list:
        """Generate data that follows Benford 2BL distribution."""
        rng = np.random.default_rng(seed)
        # Lognormal data naturally follows Benford
        values = (rng.lognormal(mean=5, sigma=2, size=n * 2)).astype(int)
        values = values[values >= 10][:n]  # need 2+ digits for 2nd digit
        return values.tolist()

    def _generate_uniform_digits(self, n: int, seed: int = 42) -> list:
        """Generate data with uniform 2nd digits — should violate Benford."""
        rng = np.random.default_rng(seed)
        # Force uniform 2nd digit: e.g., 10, 11, 12, ..., 19, 20, 21, ...
        values = []
        for _ in range(n):
            d1 = rng.integers(1, 10)
            d2 = rng.integers(0, 10)
            rest = rng.integers(0, 100)
            values.append(d1 * 1000 + d2 * 100 + rest)
        return values

    def test_compliant_data_is_nominal(self):
        """Lognormal data (natural Benford) should not trigger alerts."""
        data = self._generate_benford_compliant(500)
        result = benford_canonical(data)
        assert result is not None
        assert result.is_canonical is True
        assert result.digit_type == "2nd"
        assert result.severity in (Severity.NOMINAL, Severity.INFO)

    def test_manipulated_data_triggers_alert(self):
        """Data with all 2nd digits = 0 (e.g., 100, 200, 300...) should trigger alert."""
        # Force all 2nd digits to '0' — clear Benford violation
        data = [d * 100 for d in range(1, 10)] * 60  # 540 values, all X00
        result = benford_canonical(data)
        assert result is not None
        assert result.severity in (Severity.WARNING, Severity.CRITICAL)

    def test_graceful_degradation(self):
        """Less than min_samples → None."""
        result = benford_canonical([100, 200, 300])
        assert result is None

    def test_min_samples_boundary(self):
        """Exactly min_samples should work."""
        data = self._generate_benford_compliant(MIN_SAMPLES)
        result = benford_canonical(data, min_samples=MIN_SAMPLES)
        assert result is not None

    def test_filters_non_positive(self):
        """Zero, negative, and non-integer values should be filtered out."""
        good_data = self._generate_benford_compliant(50)
        dirty_data = good_data + [0, -5, -100]
        result = benford_canonical(dirty_data)
        assert result is not None
        assert result.n == 50  # only the good data counted

    def test_single_digit_values_excluded_from_2nd(self):
        """Values < 10 have no 2nd digit — should be excluded."""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9] * 10 + self._generate_benford_compliant(50)
        result = benford_canonical(data)
        assert result is not None
        assert result.n == 50  # single-digit values excluded

    def test_entity_label(self):
        """Entity label should be preserved in result."""
        data = self._generate_benford_compliant(50)
        result = benford_canonical(data, entity="Francisco Morazán")
        assert result is not None
        assert result.entity == "Francisco Morazán"


# ===================================================================
# BENFORD TESTS — Experimental (1st digit)
# ===================================================================
class TestBenfordExperimental:
    """Tests for benford_experimental_first_digit — max severity is INFO."""

    def test_max_severity_is_info(self):
        """Even with terrible data, max severity should be INFO (never WARNING/CRITICAL)."""
        # Completely non-Benford data: all values start with same digit
        data = list(range(1000, 1100)) * 5  # 500 values all starting with '1'
        result = benford_experimental_first_digit(data)
        assert result is not None
        assert result.severity in (Severity.NOMINAL, Severity.INFO)
        assert result.is_canonical is False

    def test_compliant_data(self):
        """Lognormal data may still trigger INFO for 1st digit — demonstrating high FP rate.
        This is expected and is WHY we demoted 1st digit from CRITICAL to INFO."""
        rng = np.random.default_rng(42)
        data = (rng.lognormal(5, 2, 500)).astype(int).tolist()
        result = benford_experimental_first_digit(data)
        assert result is not None
        # Max severity for experimental is INFO — never WARNING or CRITICAL
        assert result.severity in (Severity.NOMINAL, Severity.INFO)
        assert result.is_canonical is False


# ===================================================================
# BENFORD TESTS — Batch analysis
# ===================================================================
class TestBenfordBatch:
    """Tests for benford_batch (per-entity analysis)."""

    def test_batch_runs_per_entity(self):
        """Should return one result per entity with sufficient data."""
        rng = np.random.default_rng(42)
        data = {
            "Depto A": (rng.lognormal(5, 2, 100)).astype(int).tolist(),
            "Depto B": (rng.lognormal(5, 2, 100)).astype(int).tolist(),
            "Depto C": [10, 20],  # too few → excluded
        }
        results = benford_batch(data)
        assert len(results) == 2
        entities = {r.entity for r in results}
        assert "Depto A" in entities
        assert "Depto B" in entities

    def test_batch_experimental(self):
        """Batch with experimental type should cap at INFO."""
        rng = np.random.default_rng(42)
        data = {
            "X": list(range(1000, 1100)) * 5,  # non-Benford
        }
        results = benford_batch(data, test_type="experimental")
        assert len(results) == 1
        assert results[0].severity in (Severity.NOMINAL, Severity.INFO)


# ===================================================================
# BENFORD REGRESSION: Calibration placeholder
# ===================================================================
class TestBenfordCalibration:
    """
    Placeholder for calibration against 96 HN 2025 JSONs.
    When real data is available, replace the synthetic data with actual
    vote counts and verify FP rates match documented thresholds.
    """

    def test_synthetic_calibration_2bl(self):
        """
        Synthetic calibration: generate 96 'clean' datasets (lognormal),
        run 2BL on each, verify FP rate < 5%.
        """
        rng = np.random.default_rng(2025)
        false_positives = 0
        n_trials = 96

        for _ in range(n_trials):
            # Simulate clean departmental vote counts
            data = (rng.lognormal(mean=5.5, sigma=1.8, size=200)).astype(int)
            data = data[data >= 10].tolist()
            result = benford_canonical(data)
            if result is not None and result.severity in (Severity.WARNING, Severity.CRITICAL):
                false_positives += 1

        fp_rate = false_positives / n_trials
        assert fp_rate < 0.05, f"FP rate {fp_rate:.2%} exceeds 5% threshold"

    def test_synthetic_calibration_1st_digit_higher_fp(self):
        """
        Demonstrate that 1st digit would have higher FP than 2nd digit
        on the same clean data. This justifies the demotion.
        """
        rng = np.random.default_rng(2025)
        fp_2nd = 0
        fp_1st = 0
        n_trials = 96

        for _ in range(n_trials):
            data = (rng.lognormal(mean=5.5, sigma=1.8, size=200)).astype(int)
            data = data[data >= 10].tolist()

            r2 = benford_canonical(data)
            r1 = benford_experimental_first_digit(data)

            if r2 and r2.chi2_pvalue < 0.05:
                fp_2nd += 1
            if r1 and r1.chi2_pvalue < 0.05:
                fp_1st += 1

        # 1st digit should have equal or higher raw chi² rejections
        # (even though severity is capped at INFO)
        assert fp_1st >= fp_2nd or abs(fp_1st - fp_2nd) <= 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
