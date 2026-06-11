# CENTINEL — Public Transparency Statement
# Declaración Pública de Transparencia

**Effective / Vigente desde:** June 10, 2026
**Repository / Repositorio:** https://github.com/VectisDev/centinel

> This statement is published proactively so that any interested party can
> evaluate CENTINEL before we ask them to trust any of our findings.
> We update it whenever any material fact changes.
>
> Esta declaración se publica de forma preventiva para que cualquier
> parte interesada pueda evaluar CENTINEL antes de que le pidamos que
> confíe en cualquiera de nuestros hallazgos. La actualizamos cada vez
> que cambia cualquier hecho relevante.

---

## 1. What CENTINEL is / Qué es CENTINEL

CENTINEL is **public electoral evidence preservation infrastructure**.
It is not an electoral authority, an election observer, or an arbiter
of disputes. It captures publicly published electoral data, chains it
cryptographically, and anchors it to Bitcoin so that any third party
can verify — offline, independently, without our cooperation — that
the data was not altered after publication.

CENTINEL es **infraestructura de preservación de evidencia electoral
pública**. No es una autoridad electoral, un observador, ni un árbitro
de disputas. Captura datos electorales publicados públicamente, los
encadena criptográficamente y los ancla a Bitcoin para que cualquier
tercero pueda verificar — offline, de forma independiente y sin nuestra
cooperación — que los datos no fueron alterados después de su publicación.

---

## 2. What we do NOT claim / Lo que NO afirmamos

- We do **not** assert fraud in any election.
  No afirmamos fraude en ninguna elección.
- We do **not** interpret anomalies — we detect and preserve them.
  No interpretamos anomalías — las detectamos y las preservamos.
- We do **not** have access to physical ballots, voting machines, or
  any non-public data source.
  No tenemos acceso a actas físicas, máquinas de votación, ni ninguna
  fuente de datos no pública.
- The HN 2025 analysis was a **retroactive forensic proof-of-concept**
  on 64 JSON files manually downloaded on December 4, 2025 — not a
  live audit.
  El análisis HN 2025 fue una **demostración forense retroactiva** sobre
  64 archivos JSON descargados manualmente el 4 de diciembre de 2025 —
  no fue una auditoría en vivo.

---

## 3. Who built it / Quién lo construyó

| Role | Person | Institution |
|------|--------|-------------|
| Lead developer | Carlos Zelaya (`VectisDev`) | Independent |
| Academic validator (pending) | Prof. Devis Alvarado | UPNFM — Mathematics Dept. |
| Fiscal custodian | Ing. Mario Roberto Zelaya Guzmán | IGETEL S.A. |

**Conflict of interest disclosure:** Carlos Zelaya and Mario Roberto
Zelaya Guzmán are uncle and nephew. IGETEL's role is limited to fiscal
custodianship for grant receipt. IGETEL has no influence over methodology,
thresholds, findings, or publication decisions. This relationship has
been disclosed publicly since June 2026.

**Declaración de conflicto de interés:** Carlos Zelaya e Ing. Mario
Roberto Zelaya Guzmán son tío y sobrino. El rol de IGETEL se limita
a la custodia fiscal para recepción de grants. IGETEL no tiene influencia
sobre la metodología, umbrales, hallazgos ni decisiones de publicación.
Esta relación ha sido divulgada públicamente desde junio de 2026.

---

## 4. Funding / Financiamiento

**Current status:** Unfunded. Zero operating cost. All development is
volunteer work.

**Estado actual:** Sin financiamiento. Costo operativo cero. Todo el
desarrollo es trabajo voluntario.

We are applying to / Estamos solicitando fondos a:
- Open Technology Fund (IFF-2026-06) — application in preparation

Any grant received will be disclosed publicly in full (funder, amount,
conditions). Operating cost remains zero by design regardless of funding
status.

Cualquier grant recibido será divulgado públicamente en su totalidad.
El costo operativo permanece en cero por diseño, sin importar el estado
del financiamiento.

---

## 5. Methodology / Metodología

- Full methodology: [`docs/research/METHODOLOGY.md`](docs/research/METHODOLOGY.md)
- 23 statistical rules: [`command_center/rules.yaml`](command_center/rules.yaml)
- Pre-registered thresholds (anti-p-hacking):
  [`docs/research/THRESHOLD_PREREGISTRATION.md`](docs/research/THRESHOLD_PREREGISTRATION.md)
- False positive analysis: [`docs/research/FALSE_POSITIVE_ANALYSIS.md`](docs/research/FALSE_POSITIVE_ANALYSIS.md)
- Statistical conventions: [`docs/stats/STATISTICAL_CONVENTIONS.md`](docs/stats/STATISTICAL_CONVENTIONS.md)

All thresholds were locked on **June 10, 2026** and anchored to Bitcoin
via OpenTimestamps. Any future modification requires a new pre-registration
with justification.

Todos los umbrales fueron bloqueados el **10 de junio de 2026** y anclados
a Bitcoin via OpenTimestamps. Cualquier modificación futura requiere un
nuevo pre-registro con justificación.

---

## 6. How to reproduce every finding / Cómo reproducir cada hallazgo

```bash
git clone https://github.com/VectisDev/centinel
make reproduce-2025-audit
```

Raw data: `tests/fixtures/hnd_2025/` (64 JSON files from CNE)
Dataset DOI: [10.5281/zenodo.20598892](https://zenodo.org/records/20598892)

---

## 7. How to audit the code / Cómo auditar el código

The full source is AGPL-3.0 licensed. Security findings can be reported
via GitHub Issues or to the maintainer directly.

OTF has been informed that a code security audit is part of our grant
application and we consent to one.

El código completo tiene licencia AGPL-3.0. Los hallazgos de seguridad
pueden reportarse via GitHub Issues o directamente al mantenedor.

---

## 8. How to find errors in our work / Cómo encontrar errores en nuestro trabajo

Open a GitHub Issue or submit a Pull Request. We take corrections
seriously and publish them prominently. If a correction changes a
previously published finding, we will say so explicitly.

Template for corrections:
> *"We reviewed [CLAIM] and confirm it identified a real issue with
> [ASPECT]. We corrected [FIX] in commit [HASH]. This [does/does not]
> change the findings on [ANALYSIS]."*

Abrir un Issue o Pull Request en GitHub. Tomamos las correcciones en
serio y las publicamos de forma destacada.

---

## 9. What we would like you to scrutinize / Qué queremos que escrutines

- The statistical methodology — [`docs/research/METHODOLOGY.md`](docs/research/METHODOLOGY.md)
- The cryptographic implementation — [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)
- The false positive rate claims — [`docs/research/FALSE_POSITIVE_ANALYSIS.md`](docs/research/FALSE_POSITIVE_ANALYSIS.md)
- The conflict of interest structure — this document, §3
- The operating cost claims — [`docs/finances/zero-cost-ledger.md`](docs/finances/zero-cost-ledger.md)

The stronger the scrutiny, the more credible the findings when they matter.

Cuanto más fuerte el escrutinio, más creíbles son los hallazgos cuando importan.

---

*This document is versioned and tracked in git. Changes are detectable.*
*Este documento está versionado y rastreado en git. Los cambios son detectables.*
