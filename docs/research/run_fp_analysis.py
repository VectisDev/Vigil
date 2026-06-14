#!/usr/bin/env python3
"""
Script de reproducibilidad — Análisis de Falsos Positivos CENTINEL dev-v12.
Reproducibility script — CENTINEL dev-v12 False Positive Analysis.

Run from repo root: PYTHONPATH=src python docs/research/run_fp_analysis.py
"""
import json, sys
import numpy as np
sys.path.insert(0, 'src')

from vigil.core.rules.benford_unified import benford_canonical, benford_experimental_first_digit
from vigil.core.rules.zscore_unified import zscore_proportion, zscore_empirical

rng = np.random.default_rng(seed=2025)
N = 500
results = {
    "benford_2bl_warning":0, "benford_2bl_critical":0,
    "benford_1st_nominal_or_info":0, "benford_1st_would_be_critical":0,
    "zscore_prop_warning":0, "zscore_prop_critical":0,
    "zscore_emp_warning":0, "zscore_emp_critical":0,
}
for _ in range(N):
    counts = (rng.lognormal(5.5, 1.8, 200)).astype(int)
    counts = counts[counts >= 10].tolist()[:100]
    if len(counts) < 30:
        continue
    r2 = benford_canonical(counts)
    if r2:
        if r2.chi2_pvalue < 0.01:
            results["benford_2bl_warning"] += 1
        if r2.chi2_pvalue < 0.01 and r2.mad > 0.012:
            results["benford_2bl_critical"] += 1
    r1 = benford_experimental_first_digit(counts)
    if r1:
        if r1.chi2_pvalue < 0.05 or r1.mad > 0.006:
            results["benford_1st_would_be_critical"] += 1
        else:
            results["benford_1st_nominal_or_info"] += 1
    p_hat = rng.uniform(0.48, 0.52)
    rz = zscore_proportion(p_hat=p_hat, p_null=0.50, n=int(rng.integers(80,200)))
    if rz and rz.p_value < 0.001:
        results["zscore_prop_critical"] += 1
    elif rz and rz.p_value < 0.01:
        results["zscore_prop_warning"] += 1
    sample = rng.normal(0.60, 0.05, 50).tolist()
    re = zscore_empirical(x=float(rng.normal(0.60,0.06)), sample=sample)
    if re and re.p_value < 0.001:
        results["zscore_emp_critical"] += 1
    elif re and re.p_value < 0.01:
        results["zscore_emp_warning"] += 1

print(f"\n=== CENTINEL FP Analysis — N={N}, seed=2025 ===")
for k,v in results.items():
    print(f"  {k:<35} {v:>4}/{N} ({v/N*100:.1f}%)")
