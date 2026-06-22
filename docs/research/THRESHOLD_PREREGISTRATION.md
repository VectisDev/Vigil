# CENTINEL — Threshold Pre-Registration
# Pre-Registro de Umbrales Estadísticos

**Status / Estado:** LOCKED — thresholds below are immutable for any electoral
event analyzed after this document's commit date.

**Propósito:** Este documento pre-registra los 23 umbrales estadísticos de
CENTINEL antes de cualquier evento electoral futuro, eliminando la posibilidad
de ajuste post-hoc (p-hacking). Cualquier modificación posterior a la fecha
de commit es detectable criptográficamente.

**Purpose:** Pre-registers CENTINEL's 23 statistical thresholds before any
future electoral event, eliminating the possibility of post-hoc adjustment
(p-hacking). Any modification after the commit date is cryptographically
detectable.

---

## Document integrity / Integridad del documento

| Field | Value |
|-------|-------|
| **Pre-registration date** | 2026-06-10 |
| **Source of truth** | `command_center/rules.yaml` |
| **rules.yaml SHA-256** | `a15df9d95d96e5f10a6935b2e5a18b71640a6008e1bcd649882453924625493f` |
| **OTS calendars used** | `bob.btc.calendar.opentimestamps.org` + `finney.calendar.eternitywall.com` |
| **rules.yaml OTS proof** | `docs/research/rules_yaml.ots` (incomplete — upgrade after Bitcoin confirmation) |
| **This document OTS proof** | `docs/research/preregistration.ots` (incomplete — upgrade after Bitcoin confirmation) |
| **Anchoring** | OpenTimestamps / Bitcoin (two independent calendars) |
| **Verification** | `sha256sum command_center/rules.yaml` must equal the hash above |

---

## Scope and applicability / Alcance y aplicabilidad

These thresholds apply to:
- All future **live** electoral event monitoring (Honduras 2029 and any
  intermediate pilot events).
- They do **not** retroactively change the interpretation of the HN 2025
  retrospective forensic analysis (which was a post-mortem proof-of-concept,
  not a pre-registered study).

Estos umbrales aplican a:
- Todo monitoreo **en vivo** de eventos electorales futuros.
- **No** cambian retroactivamente la interpretación del análisis forense
  retrospectivo HN 2025 (que fue una demostración post-mortem, no un
  estudio pre-registrado).

---

## Unified Z-score convention / Convención unificada de Z-score

All Z-score thresholds across all 23 rules use two families:

| Family | Function | Use case | Warning | Critical |
|--------|----------|----------|---------|----------|
| **A — Proportion** | `zscore_proportion()` | Vote shares, turnout rates | Z > 2.576 (p<0.01) | Z > 3.291 (p<0.001) |
| **B — Empirical** | `zscore_empirical(ddof=1)` | Counts, deltas, differences | Z > 2.576 (p<0.01) | Z > 3.291 (p<0.001) |

Reference: `docs/stats/STATISTICAL_CONVENTIONS.md`

---

## Global parameters / Parámetros globales

| Parameter | Value | Justification |
|-----------|-------|---------------|
| `chi2_p_critical` | 0.01 | Standard threshold for CRITICAL chi-squared flags |
| `benford_min_samples` | 10 | Minimum sample for any Benford test |
| `max_json_presidenciales` | 19 | Honduras: 18 departments + 1 national |
| `zscore_thresholds.warning` | 2.576 | p < 0.01 two-tailed |
| `zscore_thresholds.critical` | 3.291 | p < 0.001 two-tailed |

---

## Rule thresholds — all 23 rules / Umbrales de las 23 reglas

### Section A — Formal Statistical Tests (10 rules)

#### Rule 01 · `benford_first_digit` · Severity: CRITICAL
*Benford 1st digit + MAD + chi-squared*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_samples` | 15 | Minimum for reliable Benford test |
| `mad_warning` | 0.008 | Nigrini (2012) conformity boundary |
| `mad_critical` | 0.015 | Nigrini (2012) non-conformity threshold |
| `chi_pvalue_critical` | 0.01 | Standard alpha for CRITICAL flag |

> ⚠️ **Note:** 1st-digit Benford has ~100% false positive rate on electoral
> count data (Deckert et al. 2011). This rule is retained for documentation
> against historical literature. Use `benford_law` (2nd digit, 2BL) for
> operational alerts.

#### Rule 02 · `benford_law` · Severity: MEDIUM
*Benford 2nd digit canonical (2BL) — Mebane (2006)*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_samples` | 10 | Minimum for 2BL test |
| `deviation_pct` | 15 | Maximum % deviation from expected 2BL distribution |
| `chi_square_threshold` | 0.05 | Standard alpha for MEDIUM flag |

#### Rule 03 · `last_digit_uniformity` · Severity: CRITICAL
*Chi-squared uniformity test on last digit (0–9)*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_samples` | 20 | Minimum for 10-bucket chi-squared |
| `chi_pvalue_critical` | 0.001 | Conservative threshold — uniformity departures at 0.001 are highly significant |

#### Rule 04 · `runs_test` · Severity: CRITICAL
*Wald–Wolfowitz runs test with normal approximation*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_samples` | 30 | Minimum for normal approximation validity |
| `critical_pvalue` | 0.01 | Standard alpha |

#### Rule 05 · `participation_vote_correlation` · Severity: CRITICAL
*Pearson r between turnout and leading vote share*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_samples` | 30 | Minimum for meaningful correlation |
| `warning_r` | 0.70 | Calibrated HN 2025: observed r=0.76 → early warning |
| `critical_r` | 0.85 | Validated: not triggered in HN 2025 (r=0.76 < 0.85 ✓) |

#### Rule 06 · `geographic_dispersion` · Severity: CRITICAL
*Coefficient of Variation of vote share across departments*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `critical_cv` | 0.45 | High spatial heterogeneity threshold |
| `min_departments` | 5 | Minimum for CV meaningfulness |

#### Rule 07 · `large_numbers_convergence` · Severity: MEDIUM
*Z-score convergence between sample mean and global share*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_samples` | 30 | Minimum for Law of Large Numbers to apply |
| `zscore_family` | proportion (Family A) | Testing vote shares |
| `min_total_votes` | 200 | Minimum absolute votes |

#### Rule 08 · `participation_anomaly_advanced` · Severity: CRITICAL
*Range check + Z-score vs historical baseline*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_turnout_pct` | 70 | Calibrated HN 2025: observed min=80%, 10pp buffer |
| `max_turnout_pct` | 100 | Physical upper bound |
| `historical_mean` | 88.15 | Computed from 54 HN 2025 snapshots with valid votes |
| `historical_std` | 5.51 | Computed from 54 HN 2025 snapshots with valid votes |

#### Rule 09 · `ml_outliers` · Severity: MEDIUM
*Isolation Forest on historical vote change % series*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_samples` | 5 | Minimum history for Isolation Forest |
| `max_history` | 200 | Rolling window |
| `contamination` | 0.1 | Standard Isolation Forest default |

#### Rule 10 · `granular_anomaly` · Severity: CRITICAL
*Composite: negative deltas, Z-score, Benford by dept, reversal, turnout, sum*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `negative_delta_threshold` | 0 | Votes cannot decrease |
| `delta_pct_alert` | 3.0 | >3% change in 30 min |
| `delta_pct_time_window_minutes` | 30 | Rolling window |
| `zscore_family` | empirical (Family B) | Testing count deltas |
| `zscore_min_abs_delta` | 100 | Minimum absolute delta to trigger Z-test |
| `zscore_min_departments` | 5 | Minimum departments for Z-test |
| `benford_pvalue_threshold` | 0.05 | Per-department Benford |
| `benford_min_samples` | 50 | Minimum for department-level Benford |
| `benford_min_vote` | 10 | Minimum votes per polling station |
| `turnout_min_pct` | 0.0 | Logical lower bound |
| `turnout_max_pct` | 100.0 | Physical upper bound |
| `reversal_min_lead_margin` | 500 | Minimum lead to flag reversal |
| `reversal_time_window_minutes` | 30 | Rolling window for reversal |
| `reversal_min_negative_delta` | 100 | Minimum negative delta to flag |
| `sum_mismatch_threshold` | 1 | Tolerance: 1 vote rounding allowed |

---

### Section B — Arithmetic / Heuristic Rules (10 rules)

#### Rule 11 · `basic_diff` · Severity: HIGH
| Parameter | Value | Basis |
|-----------|-------|-------|
| `relative_vote_change_pct` | 15 | >15% relative change flags unusual jump |

#### Rule 12 · `null_blank_votes` · Severity: CRITICAL
*Calibrated HN 2025: observed null+blank = 5.73% ± 0.09%*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `warning_pct` | 8 | ~2.6σ above HN 2025 observed baseline |
| `critical_pct` | 12 | ~7σ above HN 2025 observed baseline |

#### Rule 13 · `turnout_impossible` · Severity: CRITICAL
| Parameter | Value | Basis |
|-----------|-------|-------|
| `min_turnout_pct` | 0 | Physical lower bound |
| `max_turnout_pct` | 100 | Physical upper bound |

#### Rule 14 · `snapshot_jump` · Severity: CRITICAL
| Parameter | Value | Basis |
|-----------|-------|-------|
| `max_change_pct` | 5 | >5% change in ≤10 min |
| `max_minutes` | 10 | Time window |

#### Rule 15 · `processing_speed` · Severity: HIGH
| Parameter | Value | Basis |
|-----------|-------|-------|
| `max_actas_per_15min` | 500 | Physically implausible processing rate |

#### Rule 16 · `participation_anomaly` · Severity: HIGH
| Parameter | Value | Basis |
|-----------|-------|-------|
| `scrutiny_jump_pct` | 5 | >5% single-cycle scrutiny jump |

#### Rule 17 · `trend_shift` · Severity: HIGH
| Parameter | Value | Basis |
|-----------|-------|-------|
| `threshold_percent` | 10 | >10% deviation from historical trend |
| `max_hours` | 3 | Within 3-hour window |

#### Rule 18 · `irreversibility` · Severity: HIGH
| Parameter | Value | Basis |
|-----------|-------|-------|
| `historical_participation_rate` | 0.60 | Historical HN participation baseline |

#### Rule 19 · `table_consistency` · Severity: CRITICAL
| Parameter | Value | Basis |
|-----------|-------|-------|
| `total_tolerance` | 1 | 1 vote rounding tolerance |

#### Rule 20 · `inconsistency_rate` · Severity: CRITICAL
*Calibrated HN 2025: observed baseline = 14.31% ± 0.10%*

| Parameter | Value | Basis |
|-----------|-------|-------|
| `critical_pct` | 10 | Flags anomalous state from snapshot #1 |
| `escalation_delta_pct` | 0.5 | >5σ above HN 2025 stdev (0.10%) |

---

### Section C — JSON Record Forensics (3 rules)

#### Rule 21 · `mesa_reconciliation` · Severity: CRITICAL
*SHA-256 fingerprint comparison per polling station between snapshots*

No configurable thresholds — any fingerprint mutation is flagged.
No hay umbrales configurables — cualquier mutación de huella es señalada.

#### Rule 22 · `mesa_impossibility` · Severity: CRITICAL
*Internal arithmetic coherence per JSON record*

No configurable thresholds — any arithmetic impossibility is flagged.

#### Rule 23 · `late_mesa` · Severity: WARNING/CRITICAL
*Heuristic: large batch of new polling stations appearing near closure*

| Threshold | Basis |
|-----------|-------|
| WARNING if `is_near_closed` (≥90%) OR `is_large_batch` (≥50 new stations) | Either condition alone |
| CRITICAL if BOTH conditions simultaneously | Compound signal |

---

## Modification policy / Política de modificación

Any change to any threshold in `command_center/rules.yaml` after this
document's commit date MUST be accompanied by:

1. A new version of this pre-registration document with a new commit and
   new OpenTimestamps anchor.
2. A documented justification in `docs/research/THRESHOLD_CHANGELOG.md`
   with: the old value, the new value, the statistical basis for the
   change, and whether the change affects any previously published analysis.
3. The original thresholds will always remain accessible in git history.

Cualquier cambio a cualquier umbral en `command_center/rules.yaml` después
de la fecha de commit de este documento DEBE acompañarse de:

1. Una nueva versión de este documento con nuevo commit y nuevo ancla OTS.
2. Justificación documentada en `docs/research/THRESHOLD_CHANGELOG.md`.
3. Los umbrales originales permanecen siempre accesibles en el historial git.

---

## OTS verification commands / Comandos de verificación OTS

```bash
# After Bitcoin confirmation (1-24h), upgrade incomplete proofs:
# Después de confirmación Bitcoin (1-24h), actualizar los proofs incompletos:
cd docs/research/
ots upgrade rules_yaml.ots
ots upgrade preregistration.ots

# Verify that rules.yaml matches its pre-registered hash:
# Verificar que rules.yaml coincide con su hash pre-registrado:
sha256sum command_center/rules.yaml
# Expected: a15df9d95d96e5f10a6935b2e5a18b71640a6008e1bcd649882453924625493f

# Verify the OTS proof against Bitcoin blockchain:
ots verify rules_yaml.ots -f command_center/rules.yaml
ots verify preregistration.ots -f docs/research/THRESHOLD_PREREGISTRATION.md
```

## References / Referencias

- Benford, F. (1938). The law of anomalous numbers. *Proc. Am. Philosophical Society*, 78(4), 551–572.
- Mebane, W. R. (2006). Election forensics: The second-digit Benford's law test. *APSA*.
- Deckert, J., Myagkov, M., & Ordeshook, P. C. (2011). Benford's Law and the Detection of Election Fraud. *Political Analysis*, 19(3), 245–268.
- Klimek, P., et al. (2012). Statistical detection of systematic election irregularities. *PNAS*, 109(41), 16469–16473.
- Wald, A., & Wolfowitz, J. (1940). On a test whether two samples are from the same population. *Ann. Math. Stat.*, 11(2), 147–162.
- Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation forest. *ICDM 2008*.
