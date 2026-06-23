# Composite Risk Signal (CRS) — Methodology

## What this is

CRS is an **operational indicator** used in the Vigil lab and replay views to visually guide observers (technical and non-technical) toward time windows where multiple categories of anomaly converge in the official electoral data stream.

**CRS is NOT a formal hypothesis test.** It does not produce p-values, does not test a single null hypothesis, and the thresholds that map category counts to color bands are conservative heuristics — they will be empirically calibrated against historical Honduran electoral data (HND 2017, HND 2021) before publication or institutional use.

This document exists so that any reviewer — Prof. Devis Alvarado (UPNFM), OEA, Carter Center, NDI, OTF, CNA, ASJ — can understand exactly what CRS does and does not claim.

---

## Design principle: independent categories, not weighted sums

A naive composite score that sums weighted rule activations (e.g., `Σ wᵢ × ruleᵢ`) has a problem: it conflates *severity* with *convergence*. A single severe event and several mild correlated events can produce the same total, hiding the qualitative difference between them.

Vigil instead counts how many **approximately independent categories** of anomaly fired in a given 5-minute snapshot. The categories are designed to capture distinct causal pathways:

| ID | Category | Examples of rules in this category |
|----|----------|-----------------------------------|
| A  | Cryptographic integrity        | hash chain broken, signature invalid, actas rollback, binary tampered, zero-trust bypass |
| B  | Data quality                   | partial/truncated fields, critical null rate, blank rate, inconsistency rate |
| C  | Temporal behavior              | snapshot delta, speed window, escrutinio jump, participation Z-score, timestamp drift, throttling |
| D  | Arithmetic consistency         | candidate vote reversal, percentage delta, relative vote change, duplication, forced participation |
| E  | Adversarial infrastructure     | DDoS, CDN poisoning, cache staleness, coordinated drag, concentration, vis-down |

The categories are chosen so that a single underlying cause (e.g., a server failure, a configuration error, a coordinated attack) tends to trigger rules within **one** category rather than across multiple categories. This is what justifies treating cross-category convergence as evidence beyond chance.

This is conceptually inspired by Fisher's (1925) combined-probability framework for independent evidence, but **we do not apply Fisher's test formally** — that would require pre-registered p-values per rule, established independence, and calibrated null distributions, none of which are currently available.

---

## Color mapping

| Snapshot state | Color | Meaning |
|----------------|-------|---------|
| 0 categories fired | (no color) | No anomaly detected this snapshot |
| 1 category         | Amber `#d4b066` | Isolated anomaly — may be noise, document but do not act |
| 2 categories       | Orange `#e8a04a` | Moderate convergence — manual review warranted |
| 3+ categories      | Red `#c0392b` | Strong convergence — alert |
| Any Cat A rule     | Red (direct)    | Deterministic violation, bypasses counting |

Category A (cryptographic) is treated specially because its rules are deterministic, not probabilistic: a broken hash chain has no p-value — it is either valid or it is not. A single Cat A violation is sufficient evidence of integrity failure and is colored red directly regardless of what other categories report.

---

## What CRS does NOT detect

- Sophisticated fraud whose individual rule activations all fall below their per-rule thresholds
- Fraud distributed thinly across many 5-minute snapshots such that no single snapshot exceeds the category count
- Fraud occurring before official publication (Vigil only observes the public stream)
- Vote manipulation at the polling-station level that is consistent with the published-stream invariants

CRS is one layer of a defense-in-depth methodology. Its purpose is **early operational alerting**, not forensic conclusion.

---

## Calibration roadmap

1. **Phase 0 (current)**: Conservative literature-based and operationally reasonable thresholds. Color map heuristic.
2. **Phase 1 (pending Devis Alvarado review)**: Per-rule thresholds calibrated to empirical distributions from HND 2017 and HND 2021 official electoral data streams.
3. **Phase 2 (post-calibration)**: Quantify false-positive rate of the category-count thresholds against historical "normal" elections.
4. **Phase 3 (research)**: Per-category quasi-independence verified empirically; consider migration to a formal mixture model.

Until at least Phase 1 is complete, all CRS outputs must be presented as operational signals, never as statistical claims.

---

## Implementation pointers

- `web/lab/index.html` — `_catCountFromCd()`, `precomputeLabCRS()`, `crsBandsPlugin`
- `web/replay/index.html` — `crsBandsPlugin`
- The rule engine (`evaluateCheapRules`) populates `snap._cd[ruleKey] = {level, msg}`; CRS is derived from `_cd`, never directly from raw snapshots
- Thresholds live in `TV` (rule thresholds) and inside `_catCountFromCd` (category mapping). Updating either does not require visual changes.
