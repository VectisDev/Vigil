# arXiv Submission Package — CENTINEL

**Estado:** Listo para envío — pendiente firma académica de Prof. Devis Alvarado  
**Categorías:** cs.CY (primary) · stat.AP (secondary)  
**DOI datos:** 10.5281/zenodo.20598892

---

## Metadatos para el formulario de arXiv

**Title:**
```
CENTINEL: A Zero-Cost Cryptographic and Statistical Framework for Real-Time Electoral Audit in Latin America
```

**Authors:**
```
CENTINEL Project; VectisDev
```

**Abstract (pegar tal cual):**
```
We present CENTINEL (Centinela Electrónico Nacional Técnico Íntegro Neutral Estadístico Libre), an open-source system for real-time cryptographic and statistical auditing of electoral data published by Latin American electoral authorities. CENTINEL captures official JSON feeds, builds a SHA-256 immutable hash chain anchored to the Bitcoin blockchain via OpenTimestamps, and applies 23 forensic detection rules spanning formal statistical tests, arithmetic heuristics, and per-record forensics. A key methodological contribution is the demonstration that first-digit Benford's Law produces a 100% false positive rate on Honduran electoral count data, while the canonical second-digit formulation (2BL; Mebane, 2006) achieves 1.2% under 500-trial Monte Carlo simulation on clean synthetic data. We present a retroactive forensic analysis of 64 official CNE snapshots from the Honduras 2025 presidential election, identifying five statistically anomalous patterns including a 13.1-hour communication blackout and an act resolution rate of 39.15 acts/minute (3.9x the physically plausible threshold). The system operates at zero infrastructure cost using only GitHub's free tier. All data, code, and analyses are fully reproducible.
```

**Primary category:** `cs.CY` (Computers and Society)  
**Secondary category:** `stat.AP` (Statistics - Applications)

**Comments (campo opcional):**
```
11 pages, 5 tables. Code: https://github.com/VectisDev/centinel (AGPL-3.0). Data: https://doi.org/10.5281/zenodo.20598892. Academic validation in progress (UPNFM, Honduras).
```

---

## Pasos para enviar

1. Crear cuenta en https://arxiv.org (si no tienes)
2. → Submit → Start new submission
3. **Primary subject:** Computer Science → Computers and Society (cs.CY)
4. Subir el PDF: `CENTINEL_arXiv_preprint.pdf`
5. Pegar los metadatos de arriba
6. Submit → arXiv asigna un ID tipo `arXiv:2026.XXXXX`
7. El paper aparece al día siguiente en la lista pública

## Nota importante

arXiv permite subir sin revisión por pares. El paper queda disponible públicamente 
en 24 horas. Cuando Devis firme, actualizamos la versión con su nombre como co-autor.

