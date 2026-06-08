"""
Módulo unificado de Z-score para CENTINEL.
Unified Z-score module for CENTINEL.

Resuelve la inconsistencia dev-v10 de tres variantes no justificadas.
Establece dos familias únicas: Z_prop (proporciones) y Z_emp (empírico muestral).

Resolves the dev-v10 inconsistency of three unjustified variants.
Establishes two unique families: Z_prop (proportions) and Z_emp (sample empirical).

Mathematical Convention:
    Family A — Z_prop: Z = |p̂ - p₀| / √(p₀·(1-p₀)/n)
        Used when the variable is a proportion (vote share, turnout rate).
        Reference: Agresti & Coull (1998), Wald test for proportions.

    Family B — Z_emp: Z = (x - x̄) / s, where s = std(X, ddof=1)
        Used when the variable is a count, delta, or absolute value.
        ddof=1 mandatory (Bessel correction for unbiased variance estimator).
        Reference: NIST Engineering Statistics Handbook, section 1.3.5.

Thresholds (unified, no hardcoded exceptions):
    |Z| > 2.576 → WARNING  (p < 0.01, two-tailed)
    |Z| > 3.291 → CRITICAL (p < 0.001, two-tailed)

Version: 1.0.0 — replaces dev-v10 inconsistent implementations
See: docs/stats/STATISTICAL_CONVENTIONS.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
from scipy import stats

from centinel.core.rules.severity import Severity


# ---------------------------------------------------------------------------
# Unified thresholds / Umbrales unificados
# ---------------------------------------------------------------------------
# These replace the hardcoded |Z|>3 from dev-v10 Regla 8.
# Justification: align WARNING with p<0.01 and CRITICAL with p<0.001
# across the entire engine (matches last_digit_uniformity CRITICAL at p<0.001).
Z_THRESHOLD_WARNING: float = 2.576   # p < 0.01 two-tailed
Z_THRESHOLD_CRITICAL: float = 3.291  # p < 0.001 two-tailed


# ---------------------------------------------------------------------------
# Result container / Contenedor de resultado
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ZScoreResult:
    """
    Resultado estandarizado de un cálculo de Z-score.
    Standardized result of a Z-score computation.

    Attributes:
        z: Z-score value (absolute).
        p_value: Two-tailed p-value from the standard normal.
        severity: Severity level based on unified thresholds.
        family: 'proportion' or 'empirical' — documents which convention was used.
        n: Sample size used in the computation.
        observed: Observed value (p̂ or x).
        expected: Expected value (p₀ or x̄).
        se_or_std: Standard error (Family A) or sample std (Family B).
        detail: Optional human-readable description.
    """
    z: float
    p_value: float
    severity: Severity
    family: str
    n: int
    observed: float
    expected: float
    se_or_std: float
    detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Family A: Z-score for proportions (binomial SE)
# Familia A: Z-score para proporciones (SE binomial)
# ---------------------------------------------------------------------------
def zscore_proportion(
    p_hat: float,
    p_null: float,
    n: int,
    *,
    min_samples: int = 30,
    label: str = "",
) -> Optional[ZScoreResult]:
    """
    Z-score para una proporción observada vs. una proporción esperada.
    Z-score for an observed proportion vs. an expected proportion.

    Fórmula / Formula:
        SE = √(p₀ · (1 - p₀) / n)
        Z = |p̂ - p₀| / SE
        p_value = 2 · (1 - Φ(|Z|))

    Uso / Usage:
        - Regla 7 (large_numbers_convergence): p̂ = media muestral de share por mesa,
          p₀ = share global, n = número de mesas.
        - Sub-pruebas de Regla 10 que evalúan shares de voto.

    Args:
        p_hat: Proporción observada / Observed proportion [0, 1].
        p_null: Proporción esperada bajo H₀ / Expected proportion under H₀ [0, 1].
        n: Tamaño de muestra / Sample size.
        min_samples: Mínimo de observaciones requeridas / Minimum required observations.
        label: Etiqueta descriptiva opcional / Optional descriptive label.

    Returns:
        ZScoreResult if n >= min_samples, else None (graceful degradation).

    Raises:
        ValueError: If p_hat or p_null is outside [0, 1], or n < 1.

    References:
        Agresti, A. & Coull, B. (1998). Approximate is better than exact for
        interval estimation of binomial proportions. The American Statistician, 52(2).
    """
    # --- Input validation / Validación de entrada ---
    if not (0.0 <= p_hat <= 1.0):
        raise ValueError(f"p_hat must be in [0,1], got {p_hat}")
    if not (0.0 < p_null < 1.0):
        raise ValueError(f"p_null must be in (0,1), got {p_null}")
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    # --- Graceful degradation / Degradación con gracia ---
    if n < min_samples:
        return None

    # --- Computation / Cálculo ---
    se = math.sqrt(p_null * (1.0 - p_null) / n)
    if se == 0:
        return None

    z_abs = abs(p_hat - p_null) / se
    p_value = 2.0 * (1.0 - stats.norm.cdf(z_abs))

    severity = _classify_severity(z_abs)

    return ZScoreResult(
        z=round(z_abs, 6),
        p_value=round(p_value, 8),
        severity=severity,
        family="proportion",
        n=n,
        observed=round(p_hat, 6),
        expected=round(p_null, 6),
        se_or_std=round(se, 8),
        detail=label or None,
    )


# ---------------------------------------------------------------------------
# Family B: Empirical Z-score (sample std, ddof=1)
# Familia B: Z-score empírico (std muestral, ddof=1)
# ---------------------------------------------------------------------------
def zscore_empirical(
    x: float,
    sample: Sequence[float],
    *,
    min_samples: int = 30,
    label: str = "",
) -> Optional[ZScoreResult]:
    """
    Z-score empírico de un valor x respecto a una muestra de referencia.
    Empirical Z-score of a value x with respect to a reference sample.

    Fórmula / Formula:
        x̄ = mean(sample)
        s = std(sample, ddof=1)    ← Bessel correction, mandatory
        Z = |x - x̄| / s
        p_value = 2 · (1 - Φ(|Z|))

    Cambio respecto a dev-v10 / Change from dev-v10:
        Regla 10 (granular_anomaly) usaba ddof=0 (poblacional). Ahora usa
        ddof=1 (muestral). Esto produce un σ ligeramente mayor, lo que REDUCE
        falsos positivos — cambio conservador y estadísticamente correcto.

    Uso / Usage:
        - Regla 8 (participation_anomaly_advanced): x = turnout actual,
          sample = turnout histórico del departamento.
        - Regla 10 (granular_anomaly): x = delta actual,
          sample = deltas de otros departamentos.

    Args:
        x: Valor a evaluar / Value to evaluate.
        sample: Muestra de referencia / Reference sample (list or array).
        min_samples: Mínimo de observaciones requeridas / Minimum required observations.
        label: Etiqueta descriptiva opcional / Optional descriptive label.

    Returns:
        ZScoreResult if len(sample) >= min_samples, else None (graceful degradation).

    References:
        NIST/SEMATECH (2012). Engineering Statistics Handbook, Section 1.3.5.
    """
    arr = np.asarray(sample, dtype=np.float64)

    # --- Graceful degradation / Degradación con gracia ---
    n = len(arr)
    if n < min_samples:
        return None

    mean_val = float(np.mean(arr))
    # ddof=1 is MANDATORY — Bessel correction for unbiased variance estimator.
    # dev-v10 used ddof=0 in granular_anomaly — that is now corrected.
    std_val = float(np.std(arr, ddof=1))

    if std_val == 0:
        return None

    z_abs = abs(x - mean_val) / std_val
    p_value = 2.0 * (1.0 - stats.norm.cdf(z_abs))

    severity = _classify_severity(z_abs)

    return ZScoreResult(
        z=round(z_abs, 6),
        p_value=round(p_value, 8),
        severity=severity,
        family="empirical",
        n=n,
        observed=round(x, 6),
        expected=round(mean_val, 6),
        se_or_std=round(std_val, 8),
        detail=label or None,
    )


# ---------------------------------------------------------------------------
# Severity classifier / Clasificador de severidad
# ---------------------------------------------------------------------------
def _classify_severity(z_abs: float) -> Severity:
    """
    Classify Z-score into severity level using unified thresholds.
    Clasifica Z-score en nivel de severidad usando umbrales unificados.

    Thresholds (from STATISTICAL_CONVENTIONS.md):
        |Z| > 3.291 → CRITICAL (p < 0.001)
        |Z| > 2.576 → WARNING  (p < 0.01)
        else        → NOMINAL
    """
    if z_abs > Z_THRESHOLD_CRITICAL:
        return Severity.CRITICAL
    elif z_abs > Z_THRESHOLD_WARNING:
        return Severity.WARNING
    else:
        return Severity.NOMINAL
