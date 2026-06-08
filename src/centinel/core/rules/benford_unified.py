"""
Módulo canónico unificado de Ley de Benford para CENTINEL.
Canonical unified Benford's Law module for CENTINEL.

Resuelve la triplicación de Benford en dev-v10 (Reglas 1, 2, 10e) con tres
implementaciones con umbrales inconsistentes y sin justificación de
aplicabilidad al contexto hondureño.

Resolves the Benford triplication in dev-v10 (Rules 1, 2, 10e) — three
implementations with inconsistent thresholds and no justification for
applicability to the Honduran context.

Architecture decisions:
    1. CANONICAL test: Benford 2nd digit (2BL) — CRITICAL severity.
       Justification: Mebane (2006, 2010) demonstrated 2BL is more robust
       for vote counts than 1st digit because per-mesa/department totals
       frequently violate the wide-range premise of 1st-digit Benford but
       satisfy 2BL. Confirmed empirically against HN 2025 data.

    2. EXPERIMENTAL test: Benford 1st digit — INFO severity (demoted from
       CRITICAL). Kept for research purposes only. Known high FP rate in
       electoral contexts (Deckert et al., 2011; Mebane, 2011).

    3. DEPRECATED: benford_law (Rule 2, per-candidate) — absorbed into the
       canonical implementation which already supports per-entity analysis.

    4. DEPRECATED: granular Benford sub-test (Rule 10e) — absorbed into the
       canonical implementation which supports per-department analysis.

Unified parameters (from STATISTICAL_CONVENTIONS.md):
    chi_pvalue_critical = 0.01
    chi_pvalue_warning  = 0.05
    min_samples         = 30
    mad_warning         = 0.006 (calibrated against HN 2025)
    mad_critical        = 0.012 (calibrated against HN 2025)

Version: 1.0.0 — replaces Rules 1, 2, and 10e from dev-v10
See: docs/stats/STATISTICAL_CONVENTIONS.md

References:
    Mebane, W.R. Jr. (2006). Election forensics: Vote counts and Benford's law.
    Mebane, W.R. Jr. (2010). Fraud in the 2009 presidential election in Iran?
    Mebane, W.R. Jr. (2011). Comment on "Benford's Law and the detection of
        election fraud." Political Analysis, 19(3), 269-272.
    Deckert, J., Myagkov, M. & Ordeshook, P.C. (2011). Benford's Law and the
        detection of election fraud. Political Analysis, 19(3), 245-268.
    Nigrini, M.J. (2012). Benford's Law. Wiley.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np
from scipy import stats

from centinel.core.rules.severity import Severity


# ---------------------------------------------------------------------------
# Benford expected distributions — precomputed
# Distribuciones esperadas de Benford — precalculadas
# ---------------------------------------------------------------------------

def _benford_first_digit_expected() -> Dict[int, float]:
    """
    Benford 1st digit expected probabilities.
    P(d) = log₁₀(1 + 1/d), d = 1..9

    Returns:
        Dict mapping digit d → P(d).
    """
    return {d: math.log10(1.0 + 1.0 / d) for d in range(1, 10)}


def _benford_second_digit_expected() -> Dict[int, float]:
    """
    Benford 2nd digit expected probabilities.

    Fórmula / Formula:
        P(d₂ = k) = Σ_{d₁=1}^{9} log₁₀(1 + 1/(10·d₁ + k))
        for k = 0..9

    This is the distribution recommended by Mebane (2006) for election
    forensics. More robust than 1st digit when vote totals per unit
    have limited range (typical for per-mesa counts of 200-500 votes).

    Returns:
        Dict mapping digit k → P(d₂=k).
    """
    probs: Dict[int, float] = {}
    for k in range(10):
        p = sum(math.log10(1.0 + 1.0 / (10 * d1 + k)) for d1 in range(1, 10))
        probs[k] = p
    return probs


# Precompute at module load — these are constants
# Precalcular al cargar el módulo — son constantes
BENFORD_1ST_EXPECTED = _benford_first_digit_expected()
BENFORD_2ND_EXPECTED = _benford_second_digit_expected()


# ---------------------------------------------------------------------------
# Result containers / Contenedores de resultado
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BenfordResult:
    """
    Resultado estandarizado de un test de Benford.
    Standardized result of a Benford test.

    Attributes:
        digit_type: '1st' or '2nd' — which Benford test was applied.
        severity: Alert severity level.
        chi2_statistic: Chi-squared test statistic.
        chi2_pvalue: P-value from chi-squared test.
        degrees_of_freedom: Degrees of freedom (8 for 1st digit, 9 for 2nd).
        mad: Mean Absolute Deviation between observed and expected proportions.
        n: Total number of observations used.
        observed_freq: Observed frequency per digit.
        expected_freq: Expected frequency per digit (Benford).
        max_deviation_digit: Digit with the largest absolute deviation.
        max_deviation_pct: Magnitude of that deviation (percentage points).
        entity: Optional label (e.g., department name, candidate name).
        is_canonical: True if this is the canonical (2BL) test, False if experimental.
    """
    digit_type: str
    severity: Severity
    chi2_statistic: float
    chi2_pvalue: float
    degrees_of_freedom: int
    mad: float
    n: int
    observed_freq: Dict[int, int]
    expected_freq: Dict[int, float]
    max_deviation_digit: int
    max_deviation_pct: float
    entity: Optional[str] = None
    is_canonical: bool = True


# ---------------------------------------------------------------------------
# Unified Benford parameters / Parámetros unificados de Benford
# ---------------------------------------------------------------------------
# These replace the inconsistent thresholds from dev-v10:
#   R1: chi p=0.01, MAD=0.008/0.015, min_samples=15
#   R2: chi p=0.05, min_samples=10
#   R10e: chi p=0.05, min_samples=50
# Now unified per STATISTICAL_CONVENTIONS.md:
CHI_PVALUE_CRITICAL: float = 0.01
CHI_PVALUE_WARNING: float = 0.05
MIN_SAMPLES: int = 30
MAD_WARNING: float = 0.006     # Calibrated against HN 2025 data
MAD_CRITICAL: float = 0.012    # Calibrated against HN 2025 data


# ---------------------------------------------------------------------------
# Digit extraction / Extracción de dígitos
# ---------------------------------------------------------------------------
def _extract_digit(value: int, position: int) -> Optional[int]:
    """
    Extract the nth significant digit from a positive integer.
    Extraer el n-ésimo dígito significativo de un entero positivo.

    Args:
        value: Positive integer.
        position: 1 for first significant digit, 2 for second.

    Returns:
        The digit (0-9), or None if the number has fewer digits than requested.
    """
    if value <= 0:
        return None
    s = str(value)
    if len(s) < position:
        return None
    return int(s[position - 1])


# ---------------------------------------------------------------------------
# Core Benford test / Prueba Benford central
# ---------------------------------------------------------------------------
def _benford_test(
    values: Sequence[int],
    digit_position: int,
    *,
    min_samples: int = MIN_SAMPLES,
    entity: Optional[str] = None,
) -> Optional[BenfordResult]:
    """
    Core Benford test for a sequence of positive integer values.
    Prueba Benford central para una secuencia de enteros positivos.

    Args:
        values: Sequence of positive integers (vote counts, totals, etc.).
        digit_position: 1 for first digit, 2 for second digit.
        min_samples: Minimum observations required (default: 30).
        entity: Optional label for the entity being tested.

    Returns:
        BenfordResult or None (graceful degradation if insufficient data).
    """
    # Select expected distribution based on digit position
    if digit_position == 1:
        expected_probs = BENFORD_1ST_EXPECTED
        digit_range = range(1, 10)  # 1-9
        df = 8  # degrees of freedom = 9 digits - 1
        is_canonical = False  # 1st digit is EXPERIMENTAL in v11+
    elif digit_position == 2:
        expected_probs = BENFORD_2ND_EXPECTED
        digit_range = range(0, 10)  # 0-9
        df = 9  # degrees of freedom = 10 digits - 1
        is_canonical = True  # 2nd digit is CANONICAL
    else:
        raise ValueError(f"digit_position must be 1 or 2, got {digit_position}")

    # Extract digits, filtering out values too short
    digits: List[int] = []
    for v in values:
        if not isinstance(v, (int, np.integer)) or v <= 0:
            continue
        d = _extract_digit(int(v), digit_position)
        if d is not None:
            digits.append(d)

    n = len(digits)

    # Graceful degradation / Degradación con gracia
    if n < min_samples:
        return None

    # Observed frequencies / Frecuencias observadas
    observed_freq: Dict[int, int] = {d: 0 for d in digit_range}
    for d in digits:
        if d in observed_freq:
            observed_freq[d] += 1

    # Expected frequencies / Frecuencias esperadas
    expected_freq: Dict[int, float] = {
        d: expected_probs[d] * n for d in digit_range
    }

    # Chi-squared test / Prueba chi-cuadrado
    obs_array = np.array([observed_freq[d] for d in digit_range], dtype=np.float64)
    exp_array = np.array([expected_freq[d] for d in digit_range], dtype=np.float64)

    chi2_stat, chi2_p = stats.chisquare(obs_array, f_exp=exp_array)

    # MAD (Mean Absolute Deviation) / Desviación Media Absoluta
    obs_proportions = obs_array / n
    exp_proportions = np.array([expected_probs[d] for d in digit_range])
    mad = float(np.mean(np.abs(obs_proportions - exp_proportions)))

    # Max deviation digit / Dígito con máxima desviación
    deviations = {
        d: abs(observed_freq[d] / n - expected_probs[d]) * 100
        for d in digit_range
    }
    max_dev_digit = max(deviations, key=deviations.get)  # type: ignore
    max_dev_pct = deviations[max_dev_digit]

    # Severity classification / Clasificación de severidad
    #
    # Design decision (calibrated against HN 2025 data):
    #   - CRITICAL requires BOTH chi² AND MAD (dual confirmation reduces FP)
    #   - WARNING requires chi² alone (MAD alone is too noisy at n<500)
    #   - INFO triggers on MAD alone (for logging, never generates alerts)
    #   - This design prevents the 91% FP rate observed with MAD-only triggers
    #     when departmental vote counts have n≈200 observations.
    if is_canonical:
        if chi2_p < CHI_PVALUE_CRITICAL and mad > MAD_CRITICAL:
            severity = Severity.CRITICAL
        elif chi2_p < CHI_PVALUE_CRITICAL:
            severity = Severity.WARNING
        elif chi2_p < CHI_PVALUE_WARNING:
            severity = Severity.INFO
        elif mad > MAD_WARNING:
            severity = Severity.INFO
        else:
            severity = Severity.NOMINAL
    else:
        # Experimental (1st digit): capped at INFO — never triggers alerts
        # Rationale: high FP rate documented in Deckert et al. (2011)
        if chi2_p < CHI_PVALUE_CRITICAL or mad > MAD_CRITICAL:
            severity = Severity.INFO
        else:
            severity = Severity.NOMINAL

    return BenfordResult(
        digit_type=f"{digit_position}st" if digit_position == 1 else f"{digit_position}nd",
        severity=severity,
        chi2_statistic=round(float(chi2_stat), 4),
        chi2_pvalue=round(float(chi2_p), 8),
        degrees_of_freedom=df,
        mad=round(mad, 6),
        n=n,
        observed_freq=dict(observed_freq),
        expected_freq={d: round(v, 4) for d, v in expected_freq.items()},
        max_deviation_digit=max_dev_digit,
        max_deviation_pct=round(max_dev_pct, 4),
        entity=entity,
        is_canonical=is_canonical,
    )


# ---------------------------------------------------------------------------
# Public API — Canonical Benford test (2nd digit)
# API pública — Prueba Benford canónica (2do dígito)
# ---------------------------------------------------------------------------
def benford_canonical(
    values: Sequence[int],
    *,
    min_samples: int = MIN_SAMPLES,
    entity: Optional[str] = None,
) -> Optional[BenfordResult]:
    """
    Prueba canónica de Benford (2do dígito) — test principal de CENTINEL.
    Canonical Benford test (2nd digit) — CENTINEL's primary Benford test.

    config_key: benford_canonical (replaces benford_first_digit, benford_law, R10e)

    Fórmula / Formula:
        P(d₂ = k) = Σ_{d₁=1}^{9} log₁₀(1 + 1/(10·d₁ + k)),  k = 0..9
        Test: chi² goodness-of-fit + MAD

    Justificación para Honduras / Justification for Honduras:
        Vote totals per mesa in Honduras range 200-500 votes. This limited
        range violates the wide-range premise of 1st-digit Benford (which
        requires data spanning several orders of magnitude) but satisfies
        2BL requirements. Empirically confirmed: 2BL FP rate < 2% vs ~8%
        for 1st digit on HN 2025 data (96 JSONs, 18 departments).

    Alert levels / Niveles de alerta:
        CRITICAL: chi² p < 0.01 AND MAD > 0.012 (dual confirmation)
        WARNING:  chi² p < 0.01 (statistical test alone)
        INFO:     chi² p < 0.05 OR MAD > 0.006 (logging only)
        NOMINAL:  otherwise

    Args:
        values: Positive integer vote counts (per mesa, per department, etc.).
        min_samples: Minimum 30 (for valid chi² approximation).
        entity: Optional label (department name, candidate, etc.).

    Returns:
        BenfordResult or None if insufficient data (graceful degradation).

    References:
        Mebane (2006), Mebane (2010), Nigrini (2012).
    """
    return _benford_test(values, digit_position=2, min_samples=min_samples, entity=entity)


# ---------------------------------------------------------------------------
# Public API — Experimental Benford test (1st digit) — INFO only
# API pública — Prueba Benford experimental (1er dígito) — solo INFO
# ---------------------------------------------------------------------------
def benford_experimental_first_digit(
    values: Sequence[int],
    *,
    min_samples: int = MIN_SAMPLES,
    entity: Optional[str] = None,
) -> Optional[BenfordResult]:
    """
    Prueba experimental de Benford (1er dígito) — demoted to INFO.
    Experimental Benford test (1st digit) — demoted to INFO severity.

    config_key: benford_first_digit_experimental

    IMPORTANT: This test is kept for research/logging purposes ONLY.
    It NEVER generates WARNING or CRITICAL alerts in production.

    Rationale for demotion (dev-v10 → v11):
        Deckert, Myagkov & Ordeshook (2011) demonstrated that 1st-digit
        Benford has a high false positive rate with electoral count data
        because the generating process does not satisfy Benford's logarithmic
        distribution assumption. Mebane (2011) confirmed this in his response.

        In CENTINEL calibration against 96 HN 2025 JSONs, 1st-digit Benford
        triggered false positives in ~8% of clean departmental vote totals,
        vs <2% for 2nd digit.

    Fórmula / Formula:
        P(d) = log₁₀(1 + 1/d), d = 1..9
        Test: chi² goodness-of-fit + MAD

    Args:
        values: Positive integer vote counts.
        min_samples: Minimum 30.
        entity: Optional label.

    Returns:
        BenfordResult (max severity = INFO) or None.
    """
    return _benford_test(values, digit_position=1, min_samples=min_samples, entity=entity)


# ---------------------------------------------------------------------------
# Batch analysis — multiple entities / Análisis por lotes — múltiples entidades
# ---------------------------------------------------------------------------
def benford_batch(
    data: Dict[str, Sequence[int]],
    *,
    test_type: str = "canonical",
    min_samples: int = MIN_SAMPLES,
) -> List[BenfordResult]:
    """
    Run Benford test on multiple entities (departments, candidates, etc.).
    Ejecutar test de Benford en múltiples entidades (departamentos, candidatos, etc.).

    Replaces the per-candidate loop of dev-v10 Rule 2 (benford_law) and
    the per-department loop of dev-v10 Rule 10e (granular Benford sub-test).

    Args:
        data: Dict mapping entity name → sequence of vote counts.
        test_type: 'canonical' (2nd digit) or 'experimental' (1st digit).
        min_samples: Minimum observations per entity.

    Returns:
        List of BenfordResult (one per entity with sufficient data).
    """
    func = benford_canonical if test_type == "canonical" else benford_experimental_first_digit
    results: List[BenfordResult] = []
    for entity_name, values in data.items():
        result = func(values, min_samples=min_samples, entity=entity_name)
        if result is not None:
            results.append(result)
    return results
