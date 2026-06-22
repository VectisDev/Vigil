# CENTINEL — Disinformation Response Playbook
# Manual de Respuesta a Desinformación de CENTINEL

**Audit finding addressed:** Point 9 — Disinformation playbook missing.
**Hallazgo de auditoría:** Punto 9 — Ausencia de manual anti-desinformación.

**Classification:** Internal operational document. Selected sections are
designed for public release as pre-emptive statements.
**Clasificación:** Documento operativo interno. Secciones seleccionadas
están diseñadas para liberación pública como declaraciones preventivas.

**Core posture / Postura central:**
> Transparency IS the armor. Every attack surface we expose before an
> adversary does is a vector we have already neutralized.
>
> La transparencia ES la armadura. Toda superficie de ataque que
> exponemos antes de que lo haga un adversario es un vector que ya
> hemos neutralizado.

---

## PART 1 — Pre-emptive transparency statement
## PARTE 1 — Declaración preventiva de transparencia

*This statement should be published on the project website and GitHub README
before any major electoral event. It forces adversaries to respond to our
framing rather than setting their own.*

*Esta declaración debe publicarse en el sitio del proyecto y el README de
GitHub antes de cualquier evento electoral mayor. Obliga a los adversarios
a responder a nuestro encuadre en lugar de establecer el propio.*

---

### Public statement / Declaración pública

**About CENTINEL — What it is, what it is not, and what to question**
**Sobre CENTINEL — Qué es, qué no es, y qué cuestionar**

CENTINEL is open-source software for capturing and cryptographically
preserving publicly published electoral data. It is designed to be
questioned. Here is everything a critic might want to investigate:

CENTINEL es software de código abierto para capturar y preservar
criptográficamente datos electorales publicados públicamente. Está
diseñado para ser cuestionado. Aquí está todo lo que un crítico podría
querer investigar:

**1. Who funds us / Quién nos financia:**
No external funding as of June 9, 2026. Development is unfunded volunteer work.
The fiscal custodian for grant receipt is IGETEL S.A. (Honduras). A full
conflict-of-interest declaration is published at https://github.com/VectisDev/centinel/blob/main/docs. We invite scrutiny.

**2. Who built it / Quién lo construyó:**
Carlos Zelaya (handle: VectisDev), a software engineer in Honduras, with
academic validation from Prof. Devis Alvarado (Mathematics Department,
UPNFM). No political affiliation. Source code is public and auditable.

**3. What it can prove / Qué puede probar:**
Only that publicly published data exists, was captured at a certain time,
and has or has not changed since capture. Nothing more.

**4. What it cannot prove / Qué no puede probar:**
Whether anomalies detected are the result of fraud, error, or normal
electoral process variation. Interpretation requires human expertise. We
do not provide that interpretation.

**5. How to reproduce every finding / Cómo reproducir cada hallazgo:**
```bash
git clone https://github.com/VectisDev/centinel
make reproduce-2025-audit
```
The raw data and all processing scripts are in the repository.

**6. How to find bugs in our code / Cómo encontrar errores en nuestro código:**
Open an issue or submit a pull request at https://github.com/VectisDev/centinel. We take corrections
seriously and will publish corrections prominently.

---

## PART 2 — Attack taxonomy and pre-drafted responses
## PARTE 2 — Taxonomía de ataques y respuestas pre-redactadas

### Category A — Funding and conflict-of-interest attacks
### Categoría A — Ataques de financiamiento y conflicto de intereses

---

**A1. "CENTINEL is funded by a foreign government / political party"**
**"CENTINEL está financiado por un gobierno extranjero / partido político"**

*Response:*
CENTINEL has received zero funding as of June 9, 2026. Every line of code was
written on a volunteer basis. Our fiscal sponsor for future grant
applications is IGETEL S.A., a Honduran private company. All potential
donors and institutional relationships are disclosed at https://github.com/VectisDev/centinel/blob/main/docs. The
allegation is false; if evidence exists, we invite its public presentation
so we can address it.

---

**A2. "The developer has political motivations against [party/candidate]"**
**"El desarrollador tiene motivaciones políticas contra [partido/candidato]"**

*Response:*
CENTINEL applies identical statistical rules to all candidates and all
parties. The code is public; anyone can verify it treats all candidates
symmetrically. We have published our methodology, thresholds, and
false-positive analysis publicly. Our findings on HN 2025 flagged
statistical anomalies in the data — the same software would flag identical
anomalies regardless of which candidate benefited. Political motivation
cannot be assessed from the code because the code has none.

---

**A3. "IGETEL connection = family conflict of interest / Carlos Zelaya's uncle"**
**"Conexión con IGETEL = conflicto de interés familiar / tío de Carlos Zelaya"**

*Response:*
Ing. Mario Roberto Zelaya Guzmán is the General Manager of IGETEL S.A.
and is Carlos Zelaya's uncle. This relationship is disclosed publicly and
has been since June 9, 2026. IGETEL's role is limited to fiscal custodianship
for grant receipt — they handle banking and administrative infrastructure
for grants under an agreed commission. IGETEL has no influence over the
methodology, statistical thresholds, findings, or publication decisions.
The conflict-of-interest declaration at https://github.com/VectisDev/centinel/blob/main/docs details the governance
separation. We disclosed this proactively precisely because we anticipated
this question.

---

**A4. "This is a USAID / NED / Open Society operation"**
**"Esto es una operación de USAID / NED / Open Society"**

*Response:*
We have applied to or are considering applying to these organizations for
grants, as we disclose publicly. Receiving a grant from a democracy-support
organization does not make a project's methodology wrong. The methodology
is in the code. Critique the code, not the funding source. If we receive
any grant, the amount, funder, and any conditions will be published in full.

---

### Category B — Methodological attacks
### Categoría B — Ataques metodológicos

---

**B1. "Your statistical thresholds were chosen to produce a predetermined result (p-hacking)"**
**"Sus umbrales estadísticos fueron elegidos para producir un resultado predeterminado"**

*Response:*
This is a legitimate methodological concern that we take seriously. Our
response has three parts: (1) The thresholds are documented with their
academic and calibration basis in https://github.com/VectisDev/centinel/blob/main/docs/. (2) Before any future live
electoral event, we will publish a formal threshold pre-registration to a
timestamped public record (Zenodo + OpenTimestamps) with locked thresholds
that cannot be changed after the event begins. (3) The HN 2025 analysis
is explicitly described as a methodological proof-of-concept, not a
forensic conclusion. Anyone who reproduces the analysis with different
thresholds can publish their own findings — we invite that.

---

**B2. "Your false positive rate is too high / your findings are noise"**
**"Su tasa de falsos positivos es demasiado alta / sus hallazgos son ruido"**

*Response:*
Our published 500-trial Monte Carlo analysis estimates a false positive
rate below 5% across our 23 rules. We acknowledge this sample size is
below what we would want for publication in a peer-reviewed journal, and
we have documented this limitation explicitly in [WP-CENTINEL-2026-01](docs/research/WP-CENTINEL-2026-01.md).
We are expanding the validation to 10,000 trials. In the meantime, we
encourage independent replication: the simulation code is at https://github.com/VectisDev/centinel/blob/main/docs and
anyone can run it with any seed or trial count. What we report as
anomalies are statistically significant under our calibration; whether
they are causal of anything is a human judgment we do not make.

---

**B3. "Benford's law doesn't apply to election data"**
**"La ley de Benford no aplica a datos electorales"**

*Response:*
This is a nuanced point and we agree it requires care. Our primary
Benford application is to vote totals by polling station, a context
where the academic literature (Mebane 2006–2015, Klimek et al. 2012)
suggests Benford's law can serve as an anomaly indicator rather than
a definitive fraud detector. We use Benford as one of 23 complementary
rules — no single rule is dispositive. When Benford fires, we note it;
we do not conclude fraud. The full methodological discussion is at https://github.com/VectisDev/centinel/blob/main/docs.
We welcome peer review from statisticians who disagree.

---

**B4. "The findings were already known; this is not new information"**
**"Los hallazgos ya eran conocidos; esto no es información nueva"**

*Response:*
Correct — CENTINEL does not claim to have discovered previously unknown
facts about any election. What we provide is a cryptographically
preserved, reproducible, and timestamped record of publicly published
data. The value is evidentiary preservation, not journalistic discovery.
If the findings were already known, our contribution is making them
independently verifiable by anyone with a laptop.

---

**B5. "You only looked at the national-level JSON, not the actual physical ballots"**
**"Solo miraron el JSON nacional, no las actas físicas reales"**

*Response:*
Correct, and we document this explicitly. CENTINEL audits the JSON
published by the CNE — it does not examine physical ballots, voting
machines, or any in-person process. Our scope is exactly this: the
digital data that the electoral authority chose to publish publicly.
Whether the published data matches the physical ballots is a separate
question for human observers with physical access.

---

### Category C — Technical attacks
### Categoría C — Ataques técnicos

---

**C1. "CENTINEL hacked the CNE servers"**
**"CENTINEL hackeó los servidores del CNE"**

*Response:*
CENTINEL is a data capture tool, not an intrusion tool. It sends standard
HTTP GET requests to publicly accessible CNE URLs — the same requests that
any browser makes when a citizen visits the CNE website. The CNE publishes
its results for public consumption; CENTINEL consumes them programmatically
and preserves them cryptographically. This is scraping, not hacking. Our
code is public and anyone can verify it makes no write requests to any
server.

---

**C2. "The hash chain can be forged by the operator"**
**"El hash chain puede ser falsificado por el operador"**

*Response:*
Correct — a dishonest operator with the signing key could construct a
fabricated chain. This is why we anchor the Merkle root of the chain to
Bitcoin via OpenTimestamps: the anchoring is performed by an independent
third party (the Bitcoin miners), cannot be retroactively altered, and is
verifiable by anyone with access to the Bitcoin blockchain. Once a chain
root is anchored, the operator cannot alter any prior capture without
breaking the hash chain and invalidating the OTS proof. The anchor
transactions are at https://github.com/VectisDev/centinel/blob/main/docs.

---

**C3. "Your Bitcoin anchoring only proves the data existed at anchoring time, not that it's real"**
**"Su anclaje a Bitcoin solo prueba que los datos existían al anclarlos, no que son reales"**

*Response:*
This is correct and we do not claim otherwise. The OTS proof provides a
temporal lower bound: the data existed and had a specific hash at or before
the anchor time. It does not prove the data is authentic CNE data. The
pre-capture custody envelope (TLS certificate fingerprint, IP, server
Date header) provides the provenance evidence. Both layers together —
OTS for temporal immutability, TLS for provenance — answer the combined
question.

---

**C4. "The repository could be deleted or changed on GitHub"**
**"El repositorio podría ser eliminado o modificado en GitHub"**

*Response:*
This is a valid concern and we have addressed it directly: CENTINEL
maintains continuous mirrors on Codeberg (Germany), the Internet Archive
(USA), and is targeting a third independent node. Every mirror operation
is logged publicly. If the GitHub repository is taken down, the mirrors
remain and the Internet Archive is a court-recognized preservation service.
The mirror log is at https://github.com/VectisDev/centinel/blob/main/docs.

---

**C5. "A zero-cost project cannot be credible / professional"**
**"Un proyecto de costo cero no puede ser creíble / profesional"**

*Response:*
The cost of running a service has no bearing on the quality of the
mathematics or the cryptography. Git, GnuPG, Python, and SHA-256 are
used by governments and central banks; their trustworthiness does not
depend on the compute budget of the specific user. We use the same
cryptographic primitives as the systems that secure global financial
infrastructure, running on free-tier compute. The methodology is what
matters, and it is publicly auditable.

---

### Category D — Personal attacks on the operator
### Categoría D — Ataques personales al operador

---

**D1. "Carlos Zelaya is an activist / partisan operative"**
**"Carlos Zelaya es un activista / operativo partidista"**

*Response:*
Carlos Zelaya is a software engineer. His political opinions, if any, are
irrelevant to whether SHA-256 is correctly computed or whether a chi-squared
test is correctly applied. The code is public. Critique the code. If the
methodology is wrong, demonstrate it with mathematics, not with character
attacks.

---

**D2. "The developer has no academic credentials"**
**"El desarrollador no tiene credenciales académicas"**

*Response:*
The methodology has been submitted for academic review to the Mathematics
Department of UPNFM (Prof. Devis Alvarado). Peer review is ongoing. We
invite any qualified mathematician or statistician to review the work at
https://github.com/VectisDev/centinel/blob/main/docs/ and publish their critique. The code does not become more or less
correct based on the credentials of its author — only on whether the
mathematics is sound.

---

**D3. "This is designed to undermine confidence in democratic institutions"**
**"Esto está diseñado para minar la confianza en las instituciones democráticas"**

*Response:*
The opposite is our goal. CENTINEL does not create doubt — it creates
verifiability. When data is verifiably preserved, institutions that act
correctly have nothing to fear. When doubt exists, it is because
institutions have acted in ways that cannot withstand scrutiny. Opacity
undermines democratic confidence; verifiable transparency strengthens it.
We are building infrastructure for a world where citizens can verify
electoral data for themselves rather than relying on trust alone.

---

### Category E — Honduras-specific political attacks
### Categoría E — Ataques políticos específicos de Honduras

---

**E1. "This is coordinated with the opposition [political party]"**
**"Esto está coordinado con la oposición [partido político]"**

*Response:*
CENTINEL is independent of all Honduran political parties. It has no
coordination, funding, communication, or organizational ties to any
political party in Honduras or elsewhere. The methodology applies to all
parties. If any party benefits from accurate electoral data preservation,
it is the party that behaves correctly — CENTINEL cannot control which
party that is.

---

**E2. "The CNE already audits its own data; this is redundant"**
**"El CNE ya audita sus propios datos; esto es redundante"**

*Response:*
An institution auditing itself is, by definition, not an independent
audit. The CNE's internal validation processes are valuable, and CENTINEL
does not question their good faith. However, international democratic
standards (OAS, Carter Center, OSCE) consistently recommend independent
external verification. CENTINEL provides that independence: it requires
no CNE cooperation, no institutional accreditation, and no access beyond
what the CNE publishes publicly.

---

**E3. "This will be used to fuel post-election violence / destabilization"**
**"Esto se usará para incitar violencia post-electoral / desestabilización"**

*Response:*
CENTINEL publishes data and statistical findings — it does not organize
political action, call for protests, or advocate for any outcome. The
legal, political, and civic response to any findings is the exclusive
responsibility of citizens, civil society, and legal institutions. We are
a tool; tools do not destabilize societies — the political behavior of
actors in those societies does.

---

## PART 3 — 6-Hour response protocol
## PARTE 3 — Protocolo de respuesta de 6 horas

When a coordinated attack appears in social media, press, or official
statements, the following protocol activates:

Cuando un ataque coordinado aparece en redes sociales, prensa o
declaraciones oficiales, se activa el siguiente protocolo:

```
Hour 0: DETECTION
  - Monitor: Google Alerts on "CENTINEL electoral", project handles,
    and key personnel names.
  - Classify the attack: Category A / B / C / D / E (from Part 2).
  - Activate: Carlos + 1 trusted collaborator minimum.

Hour 0–1: VERIFY
  - Is the claim factually new? Does it allege a technical or
    factual error we have not addressed?
  - If YES → convene a 30-minute technical review. If error found,
    acknowledge immediately (see E-response below).
  - If NO → proceed with response from Part 2.

Hour 1–2: DRAFT RESPONSE
  - Use the pre-drafted response from Part 2 as the base.
  - Adapt to the specific claim with specific evidence links.
  - Have at least one collaborator review before posting.

Hour 2–3: DISTRIBUTE
  - Post the response on the project's GitHub (opens a Discussion
    or issue for full transparency).
  - Post to social media (controlled handle, not personal account).
  - If the attack came from press or official sources: send a formal
    reply to the same outlet with the response text.

Hour 3–6: MONITOR AND DOCUMENT
  - Track spread of the response.
  - Document: screenshot the original attack, the response, the
    timestamp, and any replies.
  - Add to docs/transparency/DISINFO-LOG.md for public record.

Hour 6+: ESCALATE IF NEEDED
  - If the attack involves legal threats or doxxing:
    → Consult legal advisor immediately (legal-strategy-agent
      protocols apply).
    → Do NOT engage in counter-doxxing or personal responses.
  - If the attack comes from government officials:
    → Issue a formal technical statement only.
    → Copy to OTF/NDI institutional contacts if funded at that time.
```

### Special case: Error discovered in our own work
### Caso especial: Error descubierto en nuestro propio trabajo

If an attack reveals a genuine error, the response protocol CHANGES:

Si un ataque revela un error genuino, el protocolo cambia:

```
1. ACKNOWLEDGE IMMEDIATELY — same day, same channel.
   Reconocer inmediatamente — el mismo día, el mismo canal.

2. DESCRIBE WHAT WAS WRONG — in specific, non-defensive terms.
   Describir qué estaba mal — en términos específicos, sin defensivas.

3. CORRECT THE RECORD — update the repository, the methodology
   document, and any published analyses affected.
   Corregir el registro — actualizar el repositorio, el documento
   de metodología y cualquier análisis afectado.

4. EXPLAIN WHAT CHANGED — write a correction notice that explains
   what the error was, how it was found, what was corrected, and
   whether the correction changes any published findings.
   Explicar qué cambió — escribir un aviso de corrección.

5. THANK THE CRITIC — publicly. An honest correction strengthens
   credibility more than any attack can damage it.
   Agradecer al crítico — públicamente.

Template:
  "We have reviewed [CLAIM] and confirm it identified a real issue
  with [SPECIFIC ASPECT]. We have corrected [SPECIFIC FIX] in commit
  [HASH]. The correction [does/does not] change the findings on
  [SPECIFIC ANALYSIS]. We thank [CRITIC] for the scrutiny — this is
  exactly the kind of review that makes open-source forensic work
  trustworthy."
```

---

## PART 4 — Pre-event public statement template
## PARTE 4 — Plantilla de declaración pública pre-evento

*Publish 30 days before any electoral event CENTINEL will monitor.*
*Publicar 30 días antes de cualquier evento electoral que CENTINEL monitoree.*

---

**[EN]** CENTINEL is preparing to monitor the [EVENT NAME] on June 9, 2026.
Before the event, we are publishing:

1. Our full methodology: https://github.com/VectisDev/centinel/blob/main/docs/
2. Our statistical thresholds, pre-registered and timestamped: https://github.com/VectisDev/centinel/blob/main/docs/
3. Our operator identity and institutional relationships: https://github.com/VectisDev/centinel/blob/main/docs/
4. Our conflict-of-interest declaration: https://github.com/VectisDev/centinel/blob/main/docs/
5. Our false-positive analysis: https://github.com/VectisDev/centinel/blob/main/docs/
6. Instructions to independently reproduce our setup: https://github.com/VectisDev/centinel/blob/main/docs/

We welcome independent parallel monitoring by any party that wishes to
verify our findings during the event.

**[ES]** CENTINEL se prepara para monitorear [NOMBRE DEL EVENTO] el
[FECHA]. Antes del evento, publicamos:

1. Metodología completa: https://github.com/VectisDev/centinel/blob/main/docs/
2. Umbrales estadísticos, pre-registrados con timestamp: https://github.com/VectisDev/centinel/blob/main/docs/
3. Identidad del operador y relaciones institucionales: https://github.com/VectisDev/centinel/blob/main/docs/
4. Declaración de conflicto de interés: https://github.com/VectisDev/centinel/blob/main/docs/
5. Análisis de tasa de falsos positivos: https://github.com/VectisDev/centinel/blob/main/docs/
6. Instrucciones para reproducir nuestra configuración de forma independiente: https://github.com/VectisDev/centinel/blob/main/docs/

Damos la bienvenida al monitoreo paralelo independiente de cualquier
parte que desee verificar nuestros hallazgos durante el evento.

---

## PART 5 — Maintenance of this playbook
## PARTE 5 — Mantenimiento de este manual

- **Review cadence:** 6 months, and after every attack or near-attack
  incident. Cadencia de revisión: 6 meses, y tras todo incidente.
- **Owner:** Carlos Zelaya, with ratification by Prof. Devis Alvarado
  when content changes affect academic framing.
- **Versioning:** This document is versioned and tracked in git. Any
  addition of a new attack category should come with: (a) a documented
  real-world trigger, (b) a reviewed response, (c) a PR signed off by
  at least two contributors.
- **Forbidden changes:** The core posture ("transparency is the armor")
  and the error-acknowledgment protocol are non-negotiable and cannot
  be edited to produce more defensive responses.
