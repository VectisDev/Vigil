"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `src/vigil/core/stats/multiple_testing.py`.

Corrección de comparaciones múltiples para las baterías de reglas de VIGIL.

Varias reglas evalúan una familia de hipótesis a la vez (un p-valor por
candidato, por departamento o por test). Sin corrección, la tasa de falsos
positivos por familia crece con el número de pruebas: con 20 pruebas
independientes a alfa=0.05, la probabilidad de al menos un falso positivo es
~64%, no 5%.

Este módulo implementa Benjamini-Hochberg (control de FDR), que es menos
conservador que Bonferroni y es el procedimiento por defecto del proyecto para
decisiones de severidad. Bonferroni se conserva en los payloads como reporte
conservador comparativo.

Componentes detectados:
  - benjamini_hochberg
  - bonferroni

Notas:
- Implementación propia sin dependencias nuevas: `verify/` y el camino de
  verificación independiente deben poder ejecutarse con solo la biblioteca
  estándar.
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.

======================== ENGLISH ========================
File: `src/vigil/core/stats/multiple_testing.py`.

Multiple-comparisons correction for VIGIL's rule batteries.

Several rules evaluate a family of hypotheses at once (one p-value per
candidate, per department, or per test). Without correction the family-wise
false-positive rate grows with the number of tests: at 20 independent tests
with alpha=0.05, the probability of at least one false positive is ~64%, not 5%.

This module implements Benjamini-Hochberg (FDR control), which is less
conservative than Bonferroni and is the project default for severity decisions.
Bonferroni is retained in payloads as a conservative comparison figure.

Detected components:
  - benjamini_hochberg
  - bonferroni

Notes:
- Self-contained implementation with no new dependencies: `verify/` and the
  independent verification path must run on the standard library alone.
- Keep this header in sync with structural changes in the file.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

__all__ = ["benjamini_hochberg", "bonferroni"]


def _validated(pvalues: Sequence[float]) -> List[float]:
    """Coacciona a float y valida el rango [0, 1].

    English: Coerce to float and validate the [0, 1] range.
    """
    out: List[float] = []
    for p in pvalues:
        value = float(p)
        if not (0.0 <= value <= 1.0):
            raise ValueError(f"p-value out of range [0, 1]: {value!r}")
        out.append(value)
    return out


def benjamini_hochberg(pvalues: Sequence[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """Procedimiento de Benjamini-Hochberg (control de FDR).

    Devuelve `(reject, qvalues)` en el MISMO orden que la entrada.

    `qvalues[i]` es el p-valor ajustado por FDR de la hipótesis `i`, con la
    monotonía del procedimiento ya impuesta (paso ascendente desde el p-valor
    mayor). `reject[i]` es `qvalues[i] <= alpha`, que es equivalente a la regla
    step-up clásica una vez impuesta la monotonía.

    English: Benjamini-Hochberg procedure (FDR control). Returns
    `(reject, qvalues)` in the SAME order as the input. Monotonicity is enforced
    by stepping up from the largest p-value, so thresholding the q-values at
    `alpha` is equivalent to the classical step-up rule.

    Args:
        pvalues: p-valores crudos en [0, 1]. / Raw p-values in [0, 1].
        alpha: nivel de FDR deseado. / Target FDR level.

    Raises:
        ValueError: si algún p-valor cae fuera de [0, 1] o `alpha` no está en
            (0, 1]. / If any p-value is outside [0, 1] or `alpha` is not in (0, 1].
    """
    if not (0.0 < alpha <= 1.0):
        raise ValueError(f"alpha must be in (0, 1]: {alpha!r}")

    values = _validated(pvalues)
    m = len(values)
    if m == 0:
        return [], []

    # Índices ordenados por p-valor ascendente / indices sorted by ascending p.
    order = sorted(range(m), key=lambda i: values[i])

    qvalues = [0.0] * m
    running_min = 1.0
    # Recorrer de mayor a menor imponiendo monotonía / walk largest-to-smallest.
    for rank, idx in enumerate(reversed(order), start=1):
        position = m - rank + 1  # rango ascendente de este p-valor (1..m)
        adjusted = values[idx] * m / position
        running_min = min(running_min, adjusted, 1.0)
        qvalues[idx] = running_min

    reject = [q <= alpha for q in qvalues]
    return reject, qvalues


def bonferroni(pvalues: Sequence[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """Corrección de Bonferroni, conservadora, para reporte comparativo.

    English: Bonferroni correction, conservative, for comparison reporting.
    """
    if not (0.0 < alpha <= 1.0):
        raise ValueError(f"alpha must be in (0, 1]: {alpha!r}")

    values = _validated(pvalues)
    m = len(values)
    if m == 0:
        return [], []

    adjusted = [min(p * m, 1.0) for p in values]
    return [p <= alpha for p in adjusted], adjusted
