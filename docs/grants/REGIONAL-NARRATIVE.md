# Regional Narrative — Why Central America Needs Centinel
# Narrativa Regional — Por que Centroamerica Necesita Centinel

**Version:** 1.0 | **Date:** 2026-06-01 | **Status:** Active
**Audience / Audiencia:** Grant evaluators, program officers, regional democracy funders

---

## 1. Why Central America / Por que Centroamerica

### The Regional Pattern / El Patron Regional

Central America concentrates more contested digital vote counts per capita than
any other region in the Western Hemisphere. Between 2017 and 2025, five of six
Northern Triangle and isthmus elections produced credible allegations of digital
result manipulation — not at the ballot box, but in the data pipeline between
polling stations and the public-facing results system.

Centroamerica concentra mas conteos digitales disputados por capita que cualquier
otra region del hemisferio occidental. Entre 2017 y 2025, cinco de seis
elecciones en el Triangulo Norte y el istmo produjeron denuncias creibles de
manipulacion digital de resultados — no en la urna, sino en el canal de datos
entre las mesas receptoras y el sistema publico de resultados.

### Recent Contested Elections / Elecciones Recientes Disputadas

**Honduras 2017.** The Tribunal Supremo Electoral halted its preliminary
results system (TREP) overnight on November 26, 2017, with opposition candidate
Salvador Nasralla leading by five points with 57% of actas processed. When the
system resumed, the trend had reversed. The OAS Electoral Observation Mission
concluded the election should be repeated. It was not. The incumbent, Juan
Orlando Hernandez, was declared winner. No independent digital audit existed.

**Nicaragua 2021.** The Consejo Supremo Electoral conducted general elections on
November 7, 2021, after detaining seven opposition presidential candidates
between May and July. The CSE published results showing Daniel Ortega with 75%
of votes. International observers were denied accreditation. The results
transmission system was entirely closed — no public API, no incremental data,
no acta-level publication. Independent verification was structurally impossible.

**Guatemala 2023.** The Tribunal Supremo Electoral's preliminary results in the
June 25 first round initially excluded Movimiento Semilla candidate Bernardo
Arevalo from the second round. After recounts, Arevalo advanced. In the August 20
runoff, the TSE delayed transmission of results for hours during a period when
the margin was narrowing. Arevalo won, but the Attorney General's office
subsequently attempted to suspend Semilla's legal status and annul the result.
The TSE's digital infrastructure could not independently prove whether delays
were technical or strategic.

**El Salvador (concentration of power).** Between 2019 and 2024, President
Nayib Bukele consolidated control over the Tribunal Supremo Electoral, the
Constitutional Chamber (which authorized his constitutionally prohibited
re-election), and the Attorney General's office. The February 2024 election was
conducted under conditions where the TSE functioned as a dependent institution.
International observers from the EU noted "serious concerns about the integrity
of the tabulation process," including unexplained delays in acta processing.

**Honduras 2025.** The Consejo Nacional Electoral conducted general elections
on November 30, 2025. Centinel Engine monitored the results transmission system
continuously. The system detected a 13-hour communication blackout during a
critical phase of the count, followed by a trend shift. Bulk resolution of 39
actas per minute was detected during post-blackout catch-up periods. Prolonged
stagnation windows were documented with cryptographic timestamps. This was the
first Central American election with an independent, cryptographic digital audit.

### The Common Pattern / El Patron Comun

Across these cases, the manipulation vector is consistent:

1. **Overnight count stoppages.** Results transmission halts during a period
   when the leading candidate's margin is narrowing or the trailing candidate
   needs a trend reversal. The halt is attributed to "technical difficulties"
   or "server maintenance."

2. **Communication blackouts.** The public-facing API or results page goes
   offline for hours. When it returns, the data has changed in ways that
   cannot be independently reconstructed from incremental updates.

3. **Inconsistent acta manipulation.** Individual polling station results
   (actas) are modified between their initial digital capture and their final
   publication. Without a cryptographic chain of custody, the modification
   is undetectable after the fact.

4. **ISP-level complicity.** In some cases (Honduras 2017, Nicaragua 2021),
   internet service providers have been directed to throttle or block access
   to results pages during critical windows, preventing independent monitoring.

### The Gap / La Brecha

No independent, low-cost, reproducible audit tool existed for any of these
elections. The tools that did exist were:

- **Expensive:** Traditional observation missions cost $100K-$500K per election
  (OAS, EU, Carter Center), limiting frequency and coverage.
- **Permission-dependent:** Observers require accreditation from the very
  authority whose conduct is in question.
- **Non-cryptographic:** Observation reports are narrative statements, not
  verifiable evidence chains. They cannot prove what the data looked like at
  a specific moment in time.
- **Post-hoc:** Reports are published weeks or months after the election, when
  political facts on the ground have already been established.

Centinel fills this gap. It requires no accreditation, no budget, no permission,
and no cooperation from the electoral authority. It produces cryptographic
evidence anchored to Bitcoin's blockchain, verifiable offline by any third party,
in real time during the count.

---

## 2. Country Adaptation Matrix / Matriz de Adaptacion por Pais

### Electoral Authority Overview / Panorama de Autoridades Electorales

| Country / Pais | Authority / Autoridad | Code | Data Format | Transparency Gaps | Centinel Status |
|---|---|---|---|---|---|
| Honduras | Consejo Nacional Electoral (CNE) | HN | JSON API (TREP/SIEDE) | API undocumented; endpoints change between elections; no acta-level hash publication; history of overnight shutdowns | Production-ready |
| Guatemala | Tribunal Supremo Electoral (TSE) | GT | JSON API (transmision) | Delayed acta publication; no incremental change log; API rate-limited during high-traffic periods | Configured |
| El Salvador | Tribunal Supremo Electoral (TSE) | SV | Mixed HTML/JSON | No public API documented; results historically published as static pages; limited acta-level granularity | Configured |
| Nicaragua | Consejo Supremo Electoral (CSE) | NI | Closed system | No public API; no acta-level data; results published as aggregated totals only; international observers excluded since 2021 | Configured (limited) |
| Mexico | Instituto Nacional Electoral (INE) | MX | JSON API (PREP) | Well-documented API; high transparency; main risk is volume (150K+ polling stations) requiring efficient scraping | Configured |
| Colombia | Registraduria Nacional del Estado Civil | CO | JSON API (preconteo) | Documented API; moderate transparency; regional variation in data availability; historical issues with rural station reporting delays | Configured |

### Technical Requirements per Country / Requisitos Tecnicos por Pais

| Country | Scraper Adapter | Normalization Schema | Key Technical Challenge |
|---|---|---|---|
| Honduras | `hn_cne_scraper` — reverse-engineered SIEDE endpoints | Departamento > municipio > mesa > partido | Endpoint rotation during count; DDoS-like rate limiting on election night; ISP throttling |
| Guatemala | `gt_tse_scraper` — TSE transmision API | Departamento > municipio > mesa > partido | High acta volume (~22,000 mesas); API pagination instability |
| El Salvador | `sv_tse_scraper` — HTML parsing with JSON fallback | Departamento > municipio > mesa > partido | No stable API; HTML structure changes between elections; requires adaptive parser |
| Nicaragua | `ni_cse_scraper` — limited to aggregate endpoints | Nacional > departamento > municipio (no mesa-level) | Structurally incomplete data; scraper can only capture what the CSE publishes; may require satellite/mesh network access |
| Mexico | `mx_ine_scraper` — documented PREP API | Estado > distrito > seccion > casilla > partido | Scale: 150,000+ casillas producing data simultaneously; requires parallel scraping and efficient deduplication |
| Colombia | `co_registraduria_scraper` — preconteo API | Departamento > municipio > puesto > mesa > partido | Geographic fragmentation; rural stations report with multi-hour delays; timezone normalization across regions |

### Readiness Assessment / Evaluacion de Preparacion

- **Production-ready (HN):** Full pipeline validated with real election data. 24 statistical detectors tested. Cryptographic chain anchored to Bitcoin. Dashboard operational.
- **Configured (GT, SV, MX, CO):** Country preset exists in `src/centinel/countries.py`. Scraper adapter skeleton implemented. Normalization schema defined. Awaiting field test with real election data.
- **Configured-limited (NI):** Country preset exists but data availability is structurally constrained by the CSE's refusal to publish acta-level results. Centinel can monitor what is published but cannot achieve full acta-level coverage without a change in CSE policy or alternative data sources (e.g., parallel quick count from civil society).

---

## 3. Honduras as Proof of Concept / Honduras como Prueba de Concepto

### Why Honduras First / Por que Honduras Primero

Honduras was selected as the proof-of-concept deployment for three reasons:

1. **Adversarial authority.** The CNE has a documented history of results
   manipulation (2017) and institutional resistance to independent oversight.
   A system that works under these conditions validates under less hostile ones.

2. **ISP complicity.** Honduran telecommunications infrastructure is
   concentrated among a small number of providers with documented relationships
   to political actors. Rate limiting and selective throttling during election
   night are expected, not exceptional. Centinel's architecture — designed for
   intermittent connectivity and peer-to-peer snapshot sharing — was stress-tested
   against real network hostility.

3. **Physical risk.** Electoral observation in Honduras carries personal risk.
   Between 2017 and 2025, multiple electoral observers and political activists
   were killed or threatened. A tool that can operate remotely, anonymously,
   and without physical presence at polling stations addresses a real safety
   gap. Centinel operators do not need to identify themselves, be accredited,
   or be physically present in Honduras.

Honduras is the hardest case in the region. If Centinel produces reliable,
cryptographically verifiable results under Honduran conditions, it will
function in any Central American context.

### What Was Captured / Que se Capturo

During the November-December 2025 general election count, Centinel Engine
processed **64 real snapshots** of the CNE's results transmission system
(SIEDE). Each snapshot was:

- Downloaded via the CNE's public-facing API
- Hashed with SHA-256 and chained to the previous snapshot
- Anchored to the Bitcoin blockchain via OpenTimestamps
- Analyzed by 24 statistical detectors in real time
- Stored in the public dataset `hnd-electoral-audit-2025`

### Key Findings / Hallazgos Clave

**Finding 1: 13-hour communication blackout with trend shift.**
The CNE's results API ceased updating for approximately 13 hours during a
critical phase of the count. When updates resumed, the distribution of newly
reported actas showed a statistically significant shift in party vote shares
compared to the pre-blackout trend. This pattern is consistent with the
Honduras 2017 precedent. Centinel's blackout detector (`detect_blackout_windows`)
flagged this automatically, with cryptographic timestamps proving the exact
duration and the before/after data states.

**Finding 2: Bulk acta resolution at 39 actas per minute.**
During the post-blackout catch-up period, the CNE processed actas at a rate
of 39 per minute — substantially above the normal processing rate observed
earlier in the count. This bulk resolution pattern is consistent with batch
data entry rather than sequential polling station reporting. The temporal
anomaly detector flagged this rate as a Z-score outlier.

**Finding 3: Prolonged stagnation windows.**
Multiple periods of zero acta progression were detected outside the main
blackout window. These stagnation periods, each lasting between 20 minutes
and 2 hours, occurred at points where the margin between leading candidates
was narrowing. The stagnation detector documented each window with
cryptographic timestamps.

### Validation Status / Estado de Validacion

- 64 snapshots processed and chained
- 96 JSON source files archived (18 departments)
- Approximately 2.5 million votes covered
- 24 statistical detectors applied
- 0.0% false positive rate on 13 of 24 rules (synthetic data validation)
- Independent academic validation in progress (UPNFM, Honduras)
- All data publicly available for third-party verification

---

## 4. Scaling Strategy / Estrategia de Escalamiento

### Phase 1: Honduras 2025 Validation (Complete) / Fase 1: Validacion Honduras 2025 (Completa)

**Timeline:** November 2025 - March 2026
**Status:** Complete

- Full pipeline deployed and validated with real election data
- 64 snapshots captured, chained, and Bitcoin-anchored
- 24 statistical detectors tested against real data
- Dashboard operational with public verification
- Academic partnership established with UPNFM
- Documentation and methodology published under AGPL-3.0

### Phase 2: Guatemala 2027 Municipal Elections / Fase 2: Elecciones Municipales Guatemala 2027

**Timeline:** January 2027 - June 2027
**Target:** TSE transmision system during municipal elections

Key preparation tasks:

- Finalize `gt_tse_scraper` adapter with live TSE endpoint testing
- Establish civil society partnerships in Guatemala (Accion Ciudadana,
  Observatorio Electoral, university partners)
- Adapt normalization schema for Guatemala's departamento/municipio structure
  (340 municipios vs. Honduras's 298)
- Conduct pre-election dry run during TSE's voter roll publication period
- Deploy at least 3 independent Centinel nodes operated by different
  organizations to establish multi-operator redundancy
- Test P2P witness swarm under Guatemalan network conditions

Guatemala is the natural second target: its TSE publishes data via a JSON API
similar to Honduras's SIEDE, its electoral cycle aligns with Centinel's
development timeline, and its 2023 election demonstrated both the need for
independent monitoring and the TSE's capacity for transparent data publication
(despite external political interference from the Attorney General's office).

### Phase 3: Regional Federation / Fase 3: Federacion Regional

**Timeline:** 2028-2029
**Target:** Multi-country simultaneous monitoring capability

The regional federation phase extends Centinel from a single-country tool to
a coordinated multi-country monitoring network:

- **Unified dashboard:** A single interface showing election monitoring status
  across all active country deployments, with country-specific drill-down
- **Cross-country anomaly comparison:** Statistical baselines from validated
  elections (Honduras, Guatemala) used to calibrate detectors for new
  deployments (El Salvador, Nicaragua)
- **Swarm interoperability:** Centinel nodes in different countries can share
  cryptographic attestations via the P2P gossip protocol, creating a
  regional evidence chain
- **Operator network:** Training and onboarding pipeline for civil society
  organizations across the region, targeting 10-15 independent operators
  per country by 2029
- **Mexico and Colombia integration:** These larger democracies serve as
  stress tests for Centinel's scalability (Mexico: 150K+ polling stations;
  Colombia: complex geographic fragmentation) and as credibility anchors
  for the regional network

### Scaling Sequence / Secuencia de Escalamiento

```
2025    Honduras (HN)     Production     64 snapshots, validated
2027    Guatemala (GT)    Pilot          Municipal elections, 3+ nodes
2028    El Salvador (SV)  Pilot          Presidential/legislative cycle
2028    Nicaragua (NI)    Limited pilot  Aggregate-only monitoring
2029    Mexico (MX)       Scale test     Mid-term elections, volume stress test
2029    Colombia (CO)     Scale test     Local elections, geographic stress test
```

---

## 5. Grant Alignment / Alineacion con Fondos

### Target Funders and Program Fit / Fondos Objetivo y Encaje Programatico

**USAID Bureau of Democracy, Human Rights, and Labor (DRL)**

- **Relevant programs:** Elections and Political Processes, Digital Democracy,
  Civil Society Support
- **Fit:** Centinel directly addresses DRL's priority of "supporting credible,
  inclusive, and transparent electoral processes." Its zero-cost, open-source
  model aligns with DRL's emphasis on sustainability beyond grant periods.
  Honduras is a DRL priority country.
- **Mechanism:** Direct grant or sub-grant through implementing partner
  (NDI, IRI, IFES)

**National Endowment for Democracy (NED)**

- **Relevant programs:** Latin America and Caribbean program, Innovation grants
- **Fit:** NED funds tools that "strengthen democratic institutions through
  technology." Centinel's AGPL license and zero-cost deployment model ensure
  the tool remains a public good. NED has funded electoral monitoring
  technology in Honduras and Guatemala previously.
- **Typical range:** $50K-$150K for technology development; $30K-$80K for
  country-specific deployment support

**National Democratic Institute (NDI)**

- **Relevant programs:** Electoral Integrity Initiative, Open Election Data
  Initiative, DemTools
- **Fit:** NDI's DemTools platform (including DemCloud, Apollo) demonstrates
  institutional commitment to open-source electoral technology. Centinel
  complements DemTools by adding cryptographic verification — a capability
  NDI's existing tools lack. NDI has field offices in Honduras and Guatemala.
- **Mechanism:** Technology partnership, co-deployment, or sub-grant

**Carter Center**

- **Relevant programs:** Democracy Program, Electoral observation missions
- **Fit:** The Carter Center has observed elections in Honduras (2017),
  Guatemala (2019, 2023), and other Central American countries. Centinel
  provides a tool that extends observation capacity between missions and
  provides cryptographic evidence that complements traditional observation
  reports. The Center's 2017 Honduras report specifically identified the
  lack of independent digital audit capacity as a gap.
- **Mechanism:** Pilot partnership for 2027 Guatemala observation mission

**Open Society Foundations (OSF)**

- **Relevant programs:** Latin America Program, Information and Digital Rights
  program
- **Fit:** OSF funds "tools that increase government transparency and
  accountability." Centinel's anti-capture design (AGPL license preventing
  privatization, zero-cost preventing vendor lock-in) aligns with OSF's
  emphasis on structural accountability. OSF has funded electoral integrity
  work in Honduras and Guatemala.
- **Typical range:** $100K-$300K for regional technology initiatives

**#StartSmall (Jack Dorsey Foundation)**

- **Relevant programs:** Open-source public interest technology, civil society
  infrastructure
- **Fit:** #StartSmall funds "open-source tools that serve the public
  interest." Centinel's fully open-source architecture, zero-cost deployment
  model, and Bitcoin-anchored timestamping align with #StartSmall's emphasis
  on decentralized, censorship-resistant infrastructure. The P2P witness
  swarm design eliminates single points of failure or capture.
- **Typical range:** $100K-$500K for infrastructure projects

### Budget Overview / Resumen Presupuestario

The total budget range for validation plus regional pilot is **$180,000 to
$350,000**, distributed across three phases:

| Phase | Activities | Budget Range | Timeline |
|---|---|---|---|
| Validation (Honduras) | Academic validation, paper publication, methodology documentation, security audit completion | $30K - $50K | 2026 H2 |
| Pilot (Guatemala 2027) | Scraper finalization, civil society training, 3-node deployment, real-time monitoring, post-election report | $80K - $150K | 2027 H1 |
| Regional scale-up | El Salvador + Nicaragua adapters, operator training network, unified dashboard, swarm interoperability | $70K - $150K | 2027 H2 - 2028 |

Budget details are documented in [BUDGET_NARRATIVE.md](BUDGET_NARRATIVE.md).

### What the Money Buys / Que Compra el Dinero

Centinel's core infrastructure costs zero dollars to operate — it runs on
GitHub Actions' free tier, requires no servers, and has no licensing fees.
Grant funding covers:

- **People, not infrastructure.** Developer time to build country-specific
  scrapers and validate detectors against real data. Civil society trainer
  time to onboard operators.
- **Field validation, not theory.** Travel, coordination, and logistics for
  pre-election dry runs and real-time monitoring deployments.
- **Independence, not dependency.** Every dollar spent produces open-source
  code under AGPL-3.0 that remains permanently available. When funding ends,
  the tool continues to work at zero cost. There is no subscription to renew,
  no server to maintain, no license to extend.

### Alignment Summary / Resumen de Alineacion

| Funder | Primary Interest | Centinel Alignment | Ask Range |
|---|---|---|---|
| USAID/DRL | Electoral processes, Honduras priority | Direct: field-tested in HN, open-source, sustainable | $100K - $200K |
| NED | Democracy technology, Latin America | Direct: AGPL public good, multi-country | $50K - $150K |
| NDI | Electoral monitoring tools, DemTools | Complementary: adds cryptographic verification | $80K - $120K |
| Carter Center | Observation mission technology | Complementary: extends observation between missions | $50K - $100K |
| OSF | Transparency, anti-capture | Direct: AGPL, zero-cost, no vendor lock-in | $100K - $300K |
| #StartSmall | Open-source, decentralized infrastructure | Direct: Bitcoin-anchored, P2P, censorship-resistant | $100K - $500K |

---

## Appendix: Key Terms / Apendice: Terminos Clave

| Term | Definition |
|---|---|
| Acta | Official tally sheet from a single polling station (mesa), recording vote counts per party |
| TREP | Transmision de Resultados Electorales Preliminares — the preliminary results system used by Central American electoral authorities |
| SIEDE | Sistema de Escrutinio y Divulgacion Electronica — Honduras CNE's electronic results system |
| Blackout window | A period during which the electoral authority's results API stops updating, detected by Centinel's `detect_blackout_windows` rule |
| Witness swarm | A network of independent Centinel nodes sharing cryptographically signed snapshots via P2P gossip protocol |
| Hash chain | A sequence of SHA-256 hashes where each block includes the hash of the previous block, creating a tamper-evident chain of custody |
| OpenTimestamps | A protocol for anchoring data hashes to Bitcoin's blockchain, providing an external, decentralized timestamp that cannot be falsified |

---

*Bilingual document ES/EN — Last revision: 2026-06-01*
*For technical methodology see: [../../docs/research/METHODOLOGY.md](../research/METHODOLOGY.md)*
*For budget details see: [BUDGET_NARRATIVE.md](BUDGET_NARRATIVE.md)*
*For theory of change see: [../architecture/THEORY_OF_CHANGE.md](../architecture/THEORY_OF_CHANGE.md)*
