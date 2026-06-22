# Review Package for Devis / Paquete de Revision para Devis

**Date:** 2026-06-01  
**Purpose:** Academic review preparation --- statistical and methodological validation

---

## 1. What is Centinel / Que es Centinel

Centinel (formally "Centinela") is an open-source transparency-log protocol
for adversarial electoral custody. It captures periodic snapshots of
electoral data published by an official authority (e.g., Honduras' CNE),
chains them cryptographically using SHA-256, signs them with Ed25519 operator
keys, and anchors the Merkle root to Bitcoin via OpenTimestamps. The design
follows the Certificate Transparency (RFC 6962) model, with the fundamental
inversion that the publishing authority---not a network intermediary---is the
primary adversary. Centinel does not count votes, does not assert fraud, and
does not replace the electoral tribunal. It produces a cryptographically
verifiable custody record and forensic evidence trail.

Beyond the cryptographic custody layer, Centinel includes a statistical
analysis engine with 24 detection rules that flag anomalies in electoral
data. These rules range from Benford's Law tests on first-digit distributions
to temporal pattern detectors (processing speed anomalies, trend shifts,
hold-and-release patterns) and spatial consistency checks. The engine also
includes a forensic auditor module (`inconsistent_acts.py`) that tracks
special-scrutiny vote resolution with progressive injection detection and
communication blackout analysis. It is this statistical layer---not the
cryptographic core---that requires academic validation.

---

## 2. What We Need Reviewed / Que Necesitamos que Revises

We are seeking your assessment on the following specific questions. We value
honest critique over validation; knowing what is wrong or weak is more
valuable to us than confirmation.

### 2.1 Are the 24 detection rules statistically defensible?

Each rule in `src/centinel/core/rules/` implements a single statistical
detector with an `apply()` function. The rules use chi-squared tests,
Z-scores, binomial tests, Wald-Wolfowitz runs tests, Isolation Forest (ML),
and domain-specific heuristics. We need to know:

- Are the test choices appropriate for the data characteristics (count data,
  departmental aggregates, time series of cumulative totals)?
- Are there rules that are statistically redundant (testing the same
  hypothesis in different clothing)?
- Are there rules that make assumptions that do not hold for Honduran
  electoral data (e.g., sample size requirements, independence assumptions)?

### 2.2 Are the thresholds well-calibrated?

Thresholds are defined in `command_center/rules.yaml` (281 lines). Defaults
include chi-squared critical values, Z-score thresholds (typically 3-sigma),
percentage-change triggers, and minimum sample sizes. We need to know:

- Are the default thresholds likely to produce an acceptable false-positive
  rate for a national election with ~18 departments and ~20,000 mesas?
- Should thresholds be adaptive (e.g., based on historical data from
  previous elections) rather than fixed?
- Is there a principled way to set the threat-score weights (Benford anomaly
  = +25 pts, Merkle divergence = +40 pts, etc.) rather than manual tuning?

### 2.3 Is the Benford's Law application appropriate at this data scale?

We apply Benford's first-digit law to vote counts at the departmental level
and to special-scrutiny vote totals. Typical sample sizes range from hundreds
to low thousands of values per snapshot. We need to know:

- Is Benford's Law applicable to electoral count data at this granularity?
  (Literature is mixed on small-N electoral applications.)
- Is the chi-squared goodness-of-fit test the right test, or should we use
  Kuiper's test, MAD, or a Bayesian approach?
- At what minimum sample size does our Benford test become meaningful?
  We currently require >=100 snapshots before alerting---is this
  conservative enough, or too conservative?

### 2.4 Is the progressive injection detection methodology sound?

The `inconsistent_acts.py` module (1,366 lines) implements forensic tracking
for special-scrutiny vote resolution. It detects:

- Controlled progressive injection (steady drip of resolved ballots favoring
  one candidate)
- Anomalous resolution speed (ballots resolved faster than physically
  plausible)
- Asymmetric resolution distribution (resolutions consistently favor one
  candidate beyond binomial expectation)
- Hold-and-release patterns (stagnation followed by burst resolution)
- Communication blackout coinciding with trend change

We need to know:

- Are the statistical tests used for each detection pattern appropriate?
- Is the binomial test the right model for asymmetry detection, or should
  we use a different null hypothesis?
- Are there published methodologies for progressive injection detection
  that we should reference or adopt?

### 2.5 Are there statistical methods we are missing?

Given the data we have access to (time series of cumulative vote counts per
department, per candidate, with mesa-level granularity), are there additional
statistical methods that would strengthen the analysis? For example:

- Change-point detection algorithms (CUSUM, PELT)
- Spatial autocorrelation (Moran's I) for geographic anomaly detection
- Second-digit Benford analysis (Nigrini's method)
- Forensic integer analysis (terminal digit patterns beyond uniformity)
- Bayesian election forensics frameworks

---

## 3. Key Files to Review / Archivos Clave para Revision

Files are listed in priority order. Line counts are approximate.

### Priority 1: Statistical rules (the core of what needs validation)

| File | Lines | Description |
|------|-------|-------------|
| `src/centinel/core/rules/benford_first_digit_rule.py` | 289 | Benford's Law chi-squared test on first digits of vote counts. Primary statistical claim. |
| `src/centinel/core/rules/benford_law_rule.py` | 16 | Thin wrapper; delegates to benford_first_digit_rule. Check if delegation is correct. |
| `src/centinel/core/rules/last_digit_uniformity_rule.py` | 174 | Tests whether last digits of vote counts follow uniform distribution. Chi-squared test. |
| `src/centinel/core/rules/runs_test_rule.py` | 193 | Wald-Wolfowitz runs test for randomness in sequences. Check if applied correctly to this data type. |
| `src/centinel/core/rules/correlation_participation_vote_rule.py` | 162 | Pearson correlation between participation rate and vote share. Check for ecological fallacy risk. |
| `src/centinel/core/rules/granular_anomaly_rule.py` | 601 | Multi-dimensional anomaly detection at mesa level. Largest rule; most complex statistical logic. |
| `src/centinel/core/rules/ml_outliers_rule.py` | 215 | Isolation Forest for multivariate outlier detection. Check if ML is justified vs. simpler methods. |

### Priority 2: Forensic auditor module

| File | Lines | Description |
|------|-------|-------------|
| `src/auditor/inconsistent_acts.py` | 1,366 | Forensic tracker for special-scrutiny votes. Progressive injection detection, hold-and-release, Benford on special votes, blackout-with-trend-change. The most domain-specific statistical code. |

### Priority 3: Supporting rules (domain heuristics, less statistical)

| File | Lines | Description |
|------|-------|-------------|
| `src/centinel/core/rules/participation_anomaly_rule.py` | 167 | Flags departments with participation rates outside expected range. |
| `src/centinel/core/rules/participation_anomaly_advanced_rule.py` | 200 | Extended version with historical comparison and Z-score. |
| `src/centinel/core/rules/trend_shift_rule.py` | 184 | Detects sudden changes in vote-count trends between snapshots. |
| `src/centinel/core/rules/snapshot_jump_rule.py` | 139 | Flags large jumps in cumulative totals between consecutive snapshots. |
| `src/centinel/core/rules/irreversibility_rule.py` | 277 | Detects if cumulative vote counts ever decrease (should be monotonic). |
| `src/centinel/core/rules/processing_speed_rule.py` | 138 | Flags implausible mesa-processing speeds (too fast to be real). |
| `src/centinel/core/rules/turnout_impossible_rule.py` | 137 | Flags turnout >100% or other physically impossible values. |
| `src/centinel/core/rules/inconsistency_rate_rule.py` | 201 | Tracks rate of inconsistent ballot tallies across mesas. |
| `src/centinel/core/rules/large_numbers_rule.py` | 238 | Law of large numbers test for convergence in aggregated results. |
| `src/centinel/core/rules/geographic_dispersion_rule.py` | 172 | Spatial consistency checks across departments. |
| `src/centinel/core/rules/null_blank_rule.py` | 149 | Flags anomalous rates of null/blank votes. |
| `src/centinel/core/rules/table_consistency_rule.py` | 173 | Checks internal consistency of tabulation (votes <= registered voters, etc.). |
| `src/centinel/core/rules/mesa_impossibility_rule.py` | 128 | Flags physically impossible mesa-level results. |
| `src/centinel/core/rules/mesa_reconciliation_rule.py` | 122 | Checks mesa totals reconcile with department aggregates. |
| `src/centinel/core/rules/late_mesa_rule.py` | 112 | Flags mesas that report unusually late relative to peers. |
| `src/centinel/core/rules/mesas_diff_rule.py` | 141 | Diff-based anomaly detection between consecutive mesa reports. |
| `src/centinel/core/rules/basic_diff_rule.py` | 228 | Basic difference tracking between snapshots. |

### Priority 4: Configuration and infrastructure

| File | Lines | Description |
|------|-------|-------------|
| `command_center/rules.yaml` | 281 | All thresholds and parameters for detection rules. Review for calibration. |
| `src/centinel/core/rules/common.py` | 429 | Shared utilities, base classes, and the `@rule` decorator. |
| `src/centinel/core/rules/registry.py` | 112 | Rule discovery and registration. Not statistical; skip unless curious about architecture. |

---

## 4. Known Weaknesses / Debilidades Conocidas

We are aware of the following limitations. We list them here so you do not
spend time discovering what we already know, and so you can focus on what
we might be missing.

### 4.1 No real-world validation

All rules have been tested against synthetic data and limited historical
snapshots. No rule has been validated against a complete, real national
election dataset under adversarial conditions. False-positive and
false-negative rates are estimated, not measured empirically.

### 4.2 Benford applicability is uncertain at our data scale

Benford's Law is well-established for large, naturally occurring datasets.
Its applicability to electoral data is debated in the literature (Deckert,
Myagkov & Ordeshook 2011 vs. Mebane 2011). We apply it at the department
level with sample sizes in the hundreds to low thousands. We are not
confident this is sufficient for reliable inference.

### 4.3 Threshold calibration is manual

The thresholds in `rules.yaml` were set based on statistical convention
(e.g., chi-squared critical values at alpha=0.05, 3-sigma Z-scores) and
domain intuition, not based on empirical calibration against historical
Honduran election data. We have calibration scripts (`scripts/calibrate_2025.py`,
601 lines) but they have not been run against real data.

### 4.4 Ecological fallacy risk in correlation rules

The correlation between participation and vote share
(`correlation_participation_vote_rule.py`) operates at the department level.
This is a classic ecological fallacy setup---aggregate correlation does not
imply individual-level behavior. We flag it as anomaly, not as evidence of
fraud, but the distinction may be lost on non-technical consumers of the
output.

### 4.5 ML outlier detection may be unjustified

The Isolation Forest detector (`ml_outliers_rule.py`) was included for
multivariate anomaly detection. It may be overkill for the data
dimensionality we have, and its results are harder to interpret and explain
than parametric tests. We are open to removing it if simpler methods suffice.

### 4.6 Progressive injection detection is novel

The `inconsistent_acts.py` forensic module implements detection patterns
(progressive injection, hold-and-release) that we have not found in
published literature. They are based on observed patterns from Honduras
2024, not on established statistical methodology. This is the area where
we most need expert guidance.

### 4.7 Rule interdependencies are not modeled

The 24 rules are treated as independent detectors. In reality, some flag
the same underlying phenomenon (e.g., a large injection event would trigger
`snapshot_jump_rule`, `trend_shift_rule`, `processing_speed_rule`, and
potentially `benford_first_digit_rule` simultaneously). We do not model
these correlations, which may inflate apparent anomaly counts.

---

## 5. How to Run the Analysis / Como Ejecutar el Analisis

### 5.1 Environment setup

```bash
# Clone the repository
git clone <repo-url> centinel-engine
cd centinel-engine

# Create virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### 5.2 Run the full rule suite against sample data

```bash
# Run all 24 detection rules against the included sample dataset
python scripts/analyze_rules.py

# Run with verbose output showing each rule's findings
python scripts/analyze_rules.py --verbose
```

### 5.3 Replay the 2025 audit

```bash
# Replay historical snapshots and generate diff report
python scripts/replay_2025.py

# This script:
#   - Loads snapshot pairs from the data directory
#   - Computes diffs (total votes, candidate votes) between snapshots
#   - Generates a report with all detected changes
#   - Output goes to stdout or can be redirected to a file
```

### 5.4 Run calibration analysis

```bash
# Run threshold calibration against available data
python scripts/calibrate_2025.py

# This script (601 lines) evaluates rule performance
# and suggests threshold adjustments based on observed data
```

### 5.5 Run the forensic auditor

```bash
# Run the inconsistent-acts forensic tracker
# Requires snapshot data in the expected directory structure
python -m src.auditor.inconsistent_acts
```

### 5.6 Run the test suite

```bash
# Run all tests
pytest

# Run only the rules-related tests
pytest tests/ -k "rule"

# Run with coverage report
pytest --cov=src/centinel/core/rules --cov-report=term-missing
```

### 5.7 Review rule configuration

The file `command_center/rules.yaml` (281 lines) contains all configurable
thresholds. Each rule reads its parameters from this file via the `config`
argument to `apply()`. To experiment with different thresholds, edit this
file and re-run the analysis.

---

## 6. What We Are Not Asking You to Review / Que No Necesitamos que Revises

To save your time, the following areas are out of scope for this review:

- **Cryptographic layer** (SHA-256 hash chain, Ed25519 signatures, Merkle
  trees, OpenTimestamps anchoring). These use standard primitives and have
  been reviewed separately.
- **Software architecture** (FastAPI, Pydantic, deployment scripts). This
  is engineering, not statistics.
- **The whitepaper's formal proofs** (T1, T2, T3 theorems). These are
  cryptographic, not statistical. A separate reviewer will handle them.
- **Code quality or Python style.** We care about statistical correctness,
  not code aesthetics.

---

## 7. Contact and Timeline / Contacto y Cronograma

Please direct questions about rule behavior, data formats, or reproduction
issues to the project maintainer. We are available for video calls to walk
through any module in detail.

We are targeting validation before the next Honduran electoral cycle. There
is no artificial deadline---thoroughness matters more than speed.

---

**Last updated:** 2026-06-01
