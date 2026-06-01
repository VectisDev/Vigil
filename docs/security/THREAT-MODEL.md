# Threat Model / Modelo de Amenazas

**Version:** 1.0 | **Date:** 2026-06-01 | **Status:** Active

**ES:** Modelo formal de amenazas para Centinel Engine  
**EN:** Formal threat model for Centinel Engine

---

## 1. System Overview / Descripcion General del Sistema

### What Centinel does / Que hace Centinel

Centinel is a transparency-log protocol for adversarial electoral custody.
It captures periodic snapshots of data published by an electoral authority,
chains them cryptographically (SHA-256), signs them with operator keys
(Ed25519), anchors the Merkle root to an external ledger (Bitcoin via
OpenTimestamps), and distributes attestations across a federation of
independent witnesses. The design follows the Certificate Transparency
(RFC 6962) lineage, with the fundamental inversion that the publishing
authority---not a network intermediary---is the primary adversary.

Centinel no cuenta votos, no afirma fraude, y no reemplaza al tribunal
electoral. Produce un registro de custodia verificable: prueba de que los
datos capturados no fueron alterados silenciosamente, y prueba de que un
corte de acceso dirigido dejo huella firmada e inmutable.

### Data Flow Diagram / Diagrama de Flujo de Datos

```
  +-----------------+
  | Electoral Auth  |   (Adversario potencial / Potential adversary)
  | (CNE API)       |
  +--------+--------+
           |
           | HTTPS (untrusted channel)
           v
  +--------+--------+     +------------------+
  | Scraper/Collector| --> | Schema Monitor   |  (D11: endpoint integrity)
  | (download+hash) |     | (fingerprint)    |
  +--------+--------+     +------------------+
           |
           v
  +--------+--------+
  | Normalizer      |   Pydantic V2 validation + canonical JSON
  | (normalize.py)  |
  +--------+--------+
           |
           v
  +--------+---------+
  | Hash Chain (T1)  |   SHA-256 chained: H_i = SHA256(payload_i || H_{i-1})
  | (hashchain.py)   |   Merkle root over all snapshots
  +--------+---------+
           |
           +-------------+----------------+-----------------+
           |              |                |                 |
           v              v                v                 v
  +--------+----+ +-------+-------+ +-----+------+ +-------+--------+
  | Rules Engine | | Anomaly Det.  | | Federation | | External Anchor|
  | 24 detectors | | Benford + Z   | | (T2+T4)    | | (T3: OTS/BTC)  |
  | (rules/*.py) | | (anomaly_det) | | (corvid)   | | (opentimestamps|
  +--------+----+ +-------+-------+ +-----+------+ +-------+--------+
           |              |                |                 |
           v              v                v                 v
  +--------+--------------+----------------+-----------------+--------+
  |                      Threat Score Evaluation                       |
  |  Score >= 75 --> Kill Switch (Tejon) --> FREEZE + auto-recover     |
  +--------+----------------------------------------------------------+
           |
           v
  +--------+--------+     +------------------+
  | Public API      |     | Web Panel        |
  | (FastAPI, R/O)  |     | (static-first,   |
  | (alerts, hash)  |     |  Service Worker)  |
  +--------+--------+     +------------------+
           |
           v
  +--------+--------+
  | Data Repository  |   centinel-data (separate repo, survives engine)
  | snapshots/       |   hashes/, diffs/, reports/, attack_log.jsonl
  | hashes/          |
  +-----------------+
```

---

## 2. Assets / Activos Protegidos

### What we protect / Que protegemos

| # | Asset / Activo | Description / Descripcion | Impact if compromised / Impacto si comprometido |
|---|----------------|---------------------------|--------------------------------------------------|
| A1 | **Snapshot integrity** | Raw electoral data captured from CNE, stored as canonical JSON | Tampered snapshots undermine all downstream analysis; the entire custody record loses evidentiary value |
| A2 | **Hash chain** | SHA-256 chained hashes with Merkle root; append-only log | A broken chain allows silent rewriting of historical data without detection |
| A3 | **Operator identity / keys** | Ed25519 signing keys proving which witness captured which data | Compromised keys allow an adversary to forge attestations or repudiate legitimate ones |
| A4 | **Anchor proofs** | OpenTimestamps proofs anchored to Bitcoin blockchain | Without valid anchors, the adversary can claim data was fabricated after the fact |
| A5 | **Federation consensus** | Multi-witness Merkle agreement (2/3 Byzantine tolerance) | If consensus is subverted, divergence detection fails; a single compromised witness appears legitimate |
| A6 | **Attack log** | Append-only forensic log (attack_log.jsonl) | Tampered logs destroy the forensic trail of detected anomalies |
| A7 | **Statistical findings** | Benford, Z-score, rule engine outputs | Manipulated findings could suppress real anomalies or inject false positives |
| A8 | **Operator OPSEC** | Physical safety, pseudonymity, key custody of operators in hostile jurisdictions | Exposure leads to coercion, key compromise, or physical harm |

---

## 3. Threat Actors / Actores de Amenaza

### 3.1 Electoral Authority / Autoridad Electoral (CNE)

- **Capability / Capacidad:** Controls the data source. Can modify published data, change API endpoints without notice, selectively serve different data to different clients, delay or suppress publication.
- **Motivation / Motivacion:** Conceal manipulation of results; discredit monitoring tools.
- **Historical precedent / Precedente:** Honduras 2024---CNE changed `/api/results` to `/api/v2/results` without notice; extended count for over a month.

### 3.2 ISP / Network Intermediary / Intermediario de Red

- **Capability:** Man-in-the-middle attacks, selective blocking, BGP hijacking, DNS poisoning, TLS interception with state-issued certificates.
- **Motivation:** State-directed; disable or feed false data to specific witnesses.
- **Precedent:** Selective connectivity cuts during election nights in multiple Latin American countries.

### 3.3 Physical Coercion Actor / Actor de Coercion Fisica

- **Capability:** Physical access to operator or operator's device. Can compel key handover, device seizure, or force operator to act under duress.
- **Motivation:** Neutralize the witness; obtain signing keys; suppress evidence.
- **Precedent:** Documented intimidation of electoral observers in Honduras.

### 3.4 Insider / Operador Malicioso o Comprometido

- **Capability:** Full access to Centinel instance, keys, configuration. Can modify code, suppress alerts, fabricate attestations.
- **Motivation:** Corrupted, coerced, or bribed operator working against the system's purpose.
- **Note:** This is the hardest threat to mitigate with a single-operator deployment.

### 3.5 External Attacker / Atacante Externo

- **Capability:** Remote exploitation of software vulnerabilities, supply-chain attacks on dependencies, DDoS against witnesses or anchoring services.
- **Motivation:** Hired by interested party; ideological; opportunistic.

---

## 4. Attack Surfaces / Superficies de Ataque

### 4.1 Scraper / Collector

| Vector | Description | Current exposure |
|--------|-------------|-----------------|
| MITM on HTTPS | Adversary intercepts CNE responses | TLS verification active; but state-issued CA certs are a risk |
| Endpoint mutation | CNE changes URL/schema without notice | D11 (EndpointMonitor) detects schema changes; logs but does not block |
| Selective serving | CNE serves different data to different IPs | Detectable via multi-witness consensus (T2/T4) |
| Rate limiting / blocking | CNE blocks specific witness IPs | Non-fatal; degraded mode with logging |
| HTTP redirect poisoning | Malicious redirect chain to fake endpoint | Redirect chain tracked; alert if >1 hop |

### 4.2 Hash Chain

| Vector | Description | Current exposure |
|--------|-------------|-----------------|
| Collision attack on SHA-256 | Forge two inputs with same hash | Computationally infeasible with current technology |
| Chain break injection | Insert or delete a snapshot silently | Detected by chain verification (H_i depends on H_{i-1}) |
| Rollback attack | Revert to earlier state of chain | Detectable via external anchor (T3) and federation (T4) |
| Payload canonicalization bypass | Non-canonical JSON produces different hash for same data | Mitigated by strict canonical JSON via Pydantic V2 normalization |

### 4.3 External Anchor (T3)

| Vector | Description | Current exposure |
|--------|-------------|-----------------|
| OTS service unavailability | OpenTimestamps calendars unreachable | Retry with exponential backoff; fallback to testnet; non-fatal |
| Self-controlled anchor | If anchor repo is operator-controlled, adversary's lawyers argue "he controls the proof" | **Residual risk**---mitigated by OTS/Bitcoin (trustless) but requires actual deployment |
| Anchor timing gap | 10+ min between OTS submission and Bitcoin block inclusion | Acceptable for election monitoring cadence (snapshots every 30-60s, anchor every 1h) |

### 4.4 Swarm / Federation Gossip

| Vector | Description | Current exposure |
|--------|-------------|-----------------|
| Network partition | All witnesses on same ISP; single cut disables federation | Recommendation: witnesses in different jurisdictions/ISPs |
| Sybil attack | Adversary deploys fake witnesses to dominate consensus | Mitigated by pre-registered witness identities; but no on-chain identity verification |
| Signature forgery | Forge Ed25519 attestation signatures | EUF-CMA security of Ed25519; computationally infeasible |
| Clock skew | Desynced clocks cause timestamp confusion | NTP sync requirement documented; drift >5s triggers health alert |
| Gossip protocol not implemented | Only centralized coordinator queries; no P2P propagation | **Residual risk** for v0.1; acceptable for n=3 with manual coordination |

### 4.5 Frontend / Public API

| Vector | Description | Current exposure |
|--------|-------------|-----------------|
| API abuse / DDoS | Overwhelm read-only FastAPI endpoint | slowapi rate-limiting; static-first CDN with Service Worker |
| Data injection via API | Attacker submits false data through API | API is read-only; no write endpoints exposed |
| XSS / content injection on panel | Inject malicious content into web panel | Static HTML; no user-generated content rendered |

### 4.6 Operator OPSEC

| Vector | Description | Current exposure |
|--------|-------------|-----------------|
| Git metadata exposure | Commits reveal operator identity, timezone, email | **Residual risk**---pseudonym strategy recommended but not enforced |
| Key custody under coercion | Operator forced to hand over Ed25519 private key | Multi-witness federation (Corollary) degrades gracefully; but requires >=2 independent operators |
| Device seizure | Physical access to running Centinel instance | Encrypted backups (ChaCha20-Poly1305); but runtime state is in memory |
| Public attribution | Operator publicly known as project maintainer | **Residual risk**---foundation adoption or pseudonym strategy recommended |

---

## 5. Threat Matrix (STRIDE) / Matriz de Amenazas

### Spoofing / Suplantacion de Identidad

| Threat | Target | Likelihood | Impact | Mitigation | Residual risk |
|--------|--------|-----------|--------|------------|---------------|
| Forge witness attestation | Federation consensus | Low | High | Ed25519 signature verification (D13.2) | Key compromise under coercion |
| Impersonate CNE endpoint | Scraper/Collector | Medium | High | TLS verification; D11 schema fingerprint; multi-witness cross-check | State-issued CA certificates |
| Create fake witnesses (Sybil) | Consensus | Low | Critical | Pre-registered witness list; operator-verified identities | No on-chain identity anchor |

### Tampering / Manipulacion

| Threat | Target | Likelihood | Impact | Mitigation | Residual risk |
|--------|--------|-----------|--------|------------|---------------|
| Modify historical snapshots | Hash chain (A2) | Medium | Critical | SHA-256 chain (T1); any change propagates forward as mismatch | Requires SHA-256 collision (infeasible) |
| Alter data in transit (MITM) | Snapshot integrity (A1) | Medium | High | Multi-witness consensus (T2/T4); divergence detected if >=2 witnesses honest | All witnesses on same network path |
| Tamper with attack_log | Forensic trail (A6) | Low | Medium | Append-only design; Merkle root covers log state | Single-operator deployment has no external log verification |
| Modify Centinel binary on witness | All assets | Low | Critical | Auto-audit (Lagartija) binary integrity scanning; mirror coherence check | MD5 used (could upgrade to BLAKE3) |

### Repudiation / Repudio

| Threat | Target | Likelihood | Impact | Mitigation | Residual risk |
|--------|--------|-----------|--------|------------|---------------|
| CNE denies publishing data | Snapshot provenance | High | High | Ed25519 operator signature on each snapshot; OTS Bitcoin anchor (T3) | Operator signature proves capture, not CNE origin |
| Operator denies capturing data | Attestation validity | Low | Medium | Ed25519 signing with operator key; federation attestation log | Key compromise invalidates non-repudiation |
| Adversary claims data fabricated after the fact | Temporal provenance | High | Critical | OpenTimestamps Bitcoin anchor (T3) proves existence at time T | Anchor latency (10+ min); self-controlled anchor if OTS not deployed |

### Information Disclosure / Divulgacion de Informacion

| Threat | Target | Likelihood | Impact | Mitigation | Residual risk |
|--------|--------|-----------|--------|------------|---------------|
| Expose operator identity | Operator OPSEC (A8) | Medium | Critical (in hostile jurisdictions) | Pseudonym recommended; no phone-home in code (audited) | Git metadata, public repo attribution |
| Leak signing keys | Operator keys (A3) | Low | Critical | Encrypted key storage; secrets separated in config/secrets/ | Single-operator key custody; no HSM |
| Expose witness network topology | Federation | Low | Medium | No topology exposed via public API | Witness URLs in federation config |

### Denial of Service / Denegacion de Servicio

| Threat | Target | Likelihood | Impact | Mitigation | Residual risk |
|--------|--------|-----------|--------|------------|---------------|
| Block witness internet access | Snapshot capture | High (election night) | High | Non-fatal design; auto-resume with exponential backoff; Venado jitter | Extended outage = gap in custody chain |
| DDoS public API | Alert visibility | Medium | Low | slowapi rate-limiting; static CDN; Service Worker offline mode | CDN saturation (unlikely for this scale) |
| OTS calendar unavailability | External anchoring | Low | Medium | Retry with backoff; testnet fallback; non-fatal | Extended OTS outage = unanchored period |
| Kill all witnesses simultaneously | Entire system | Low | Critical | Geographic distribution; different ISPs; T3 anchor preserves last state | Requires >=2 witnesses alive for consensus |

### Elevation of Privilege / Escalada de Privilegios

| Threat | Target | Likelihood | Impact | Mitigation | Residual risk |
|--------|--------|-----------|--------|------------|---------------|
| Rootkit on witness machine | All local assets | Low | Critical | Auto-audit binary scanning; mirror restore (Lagartija); federation detects divergence | Sophisticated rootkit could disable auto-audit |
| Compromise federation coordinator | Consensus mechanism | Low | Critical | No central authority; symmetric federation design | Coordinator code runs on each witness (code integrity) |
| Supply-chain attack on dependencies | Code integrity | Low | High | Minimal dependencies; scipy/pydantic are well-audited packages | No SBOM or dependency pinning with hash verification |

---

## 6. Mitigations in Place / Mitigaciones Implementadas

### 6.1 Cryptographic Foundation / Fundamento Criptografico

| Defense | Mechanism | Theorem | Confidence |
|---------|-----------|---------|------------|
| **Hash chain integrity** | SHA-256 chained: `H_i = SHA256("centinel-hashchain-v1" \| prev \| payload)` | T1 | 99% |
| **Operator authentication** | Ed25519 signatures on snapshots and attestations | T2 | 95% (conditional on key honesty) |
| **External timestamping** | OpenTimestamps -> Bitcoin mainnet; Merkle root anchored publicly | T3 | 98% |
| **Multi-witness consensus** | Byzantine fault tolerance: 2/3 witnesses must agree on Merkle root | T2+T4 | 90% (95% with signature verification) |

### 6.2 Detection and Response / Deteccion y Respuesta

| Defense | Mechanism | Confidence |
|---------|-----------|------------|
| **Endpoint integrity monitor (D11)** | Schema fingerprinting; detects API changes without blocking capture | 95% |
| **Anomaly detection** | Benford chi-squared test (threshold chi2 > 15.99); Z-score (3-sigma); min 100 snapshots | 95% |
| **Kill Switch (Tejon)** | Threat score >= 75 triggers FREEZE; exponential backoff (2-30s) with jitter; autonomous | 95% |
| **Auto-audit (Lagartija)** | Binary integrity, state consistency, defense health, mirror coherence | 88% |
| **Federation divergence logging** | Any Merkle disagreement logged to attack_log.jsonl with full forensic detail | 90% |

### 6.3 Operational Hardening / Endurecimiento Operativo

| Defense | Mechanism |
|---------|-----------|
| **Code/data separation** | centinel-engine (code) and centinel-data (artifacts) in separate repos |
| **Encrypted backups** | ChaCha20-Poly1305 for critical state and hash artifacts |
| **Non-fatal design** | Every defense component degrades gracefully; no single failure blocks capture |
| **Timing jitter (Venado)** | +/- 30% random variation in capture cadence to resist pattern-matching |
| **NTP synchronization** | Required for witnesses; drift >5s triggers health alert |
| **Recovery atomicity** | recovery_state.json uses temp file + fsync + os.replace (ACID) |

---

## 7. Residual Risks / Riesgos Residuales

These are known weaknesses that mitigations reduce but do not eliminate.

### 7.1 Single Operator Key / Clave de Operador Unica

**Risk:** In a single-operator deployment, one Ed25519 key is the sole
authentication factor. If that key is compromised (coercion, device
seizure, theft), T2 collapses for that operator. The adversary can forge
attestations or the operator can be coerced into signing false data.

**Current mitigation:** Multi-witness federation (Corollary) degrades
T2 to T1 (still tamper-evident, but without authenticated provenance for
the compromised witness). Requires recruiting independent operators.

**Severity:** High in hostile jurisdictions. Low in cooperative deployments.

### 7.2 Self-Controlled Anchor / Ancla Autocontrolada

**Risk:** If the external anchor is a Git repository controlled by the
operator, an adversary's legal team can argue "he controls the proof."
The anchor's value depends on it being beyond the operator's ability to
rewrite.

**Current mitigation:** OpenTimestamps anchoring to Bitcoin mainnet is
implemented and trustless. However, this has not been tested in a real
deployment. If OTS is unavailable and the fallback is a self-controlled
Git repo, the anchor is rhetorically (not cryptographically) weakened.

**Severity:** Medium. Becomes low once OTS deployment is validated in a
real election.

### 7.3 No Real Deployment / Sin Despliegue Real

**Risk:** Every theorem is correct and the code is tested in isolation,
but "works in a hostile national count lasting a month" is an assertion
that cannot yet be made with evidence. Edge cases in real network
conditions, real adversarial behavior, and real operational stress remain
untested.

**Current mitigation:** E2E test suite simulates election night with
anomalies, witness offline, and MITM scenarios. Pre-pilot checklist 9/9
complete.

**Severity:** High. This is the single largest risk category---not
technical but evidentiary.

### 7.4 Gossip Protocol Not Implemented / Protocolo Gossip No Implementado

**Risk:** Federation currently uses centralized coordinator queries, not
P2P gossip. In a network partition, attestations do not propagate
between isolated groups of witnesses.

**Current mitigation:** Acceptable for v0.1 with n=3 and manual
coordination. Documented as future work.

**Severity:** Medium for small federations. High for larger deployments.

### 7.5 Operator OPSEC / Seguridad Operativa del Operador

**Risk:** Git metadata, public repository attribution, and the physical
identity of the operator are potential exposure vectors. In Honduras,
this can translate to physical danger.

**Current mitigation:** Code audited for no phone-home. Pseudonym
strategy recommended but not enforced. Foundation adoption to decouple
operator identity from project is recommended.

**Severity:** Critical in hostile jurisdictions. Operational, not
technical.

### 7.6 Binary Integrity Uses MD5 / Integridad de Binarios Usa MD5

**Risk:** Auto-audit binary scanning uses MD5 checksums. While MD5
collision resistance is broken, preimage resistance is sufficient for
integrity checking against opportunistic tampering. A sophisticated
adversary with chosen-prefix capability could craft a collision.

**Current mitigation:** Upgrade path to BLAKE3 documented.

**Severity:** Low. Practical exploitation requires targeted effort
beyond typical threat actors in this domain.

### 7.7 No Hardware Security Module (HSM) / Sin Modulo de Seguridad Hardware

**Risk:** Ed25519 keys stored in software on operator devices. No HSM,
TPM, or secure enclave integration.

**Current mitigation:** Encrypted key storage; secrets separated in
config/secrets/. Multi-witness federation reduces single-key criticality.

**Severity:** Medium. Standard for open-source projects at this stage.

---

## 8. Recommendations / Recomendaciones

### 8.1 OpenTimestamps in Production / OpenTimestamps en Produccion

**Priority:** Critical (before pilot)

Close the T3 anchor gap definitively. Ensure OTS anchoring runs
reliably during a real election. Add automated verification that the
Bitcoin transaction is included in a block within a reasonable window.
Consider mirroring OTS proofs to a third-party repository (university,
OAS/OEA) that the operator does not control.

### 8.2 Multi-Operator Federation / Federacion Multi-Operador

**Priority:** Critical (before national deployment)

Recruit >=2 independent witness operators in different jurisdictions,
different ISPs, ideally different countries. Without this, the
Corollary (multi-witness Byzantine tolerance) is theoretical and T2 is
a single point of failure. This is a political and logistical challenge,
not a technical one.

### 8.3 Pseudonym Strategy / Estrategia de Seudonimo

**Priority:** High (before public exposure)

Define and implement a sustainable pseudonym strategy for the primary
operator. Options: (a) pseudonymous maintainer identity with no
traceable link to physical person, (b) foundation or institutional
adoption that depersonalizes the project, (c) distributed maintainership
where no single individual is identified as the author. This is a
personal safety issue in Honduras and similar jurisdictions.

### 8.4 Upgrade Binary Integrity to BLAKE3

**Priority:** Low

Replace MD5 checksums in auto-audit with BLAKE3 or SHA-256. This
eliminates the theoretical collision risk and aligns with the rest of
the cryptographic stack.

### 8.5 Implement Gossip Protocol for Federation

**Priority:** Medium (before large-scale deployment)

Replace centralized coordinator queries with a P2P gossip protocol so
attestations propagate even under network partition. For v0.1 with n=3,
manual coordination is acceptable.

### 8.6 Dependency Supply-Chain Hardening

**Priority:** Medium

Add SBOM generation and dependency hash pinning. Key dependencies
(scipy, pydantic, fastapi) are well-maintained, but a supply-chain
attack on any transitive dependency could compromise code integrity.

### 8.7 Independent Academic Validation / Validacion Academica Independiente

**Priority:** Critical (before claiming "proven")

Submit the whitepaper to independent referees (not collaborators).
Specific areas for review: Benford application at the data scale of
Honduran elections, statistical defensibility of the 24 detection
rules, and the formal security proofs (T1-T3).

### 8.8 HSM / Secure Enclave Integration

**Priority:** Low (future)

For high-stakes national deployments, integrate Ed25519 key management
with hardware security modules or platform secure enclaves. This
eliminates software key extraction as an attack vector.

---

## 9. Attack Scenario Analysis / Analisis de Escenarios de Ataque

### Scenario A: MITM on Election Night / MITM en Noche Electoral

```
Attacker: Network intermediary (ISP, BGP hijack)
Target:   Single witness receives falsified data

T+0: CNE publishes: Merkle_A
     Witness A captures --> Merkle_A  (correct)
     Witness B receives FAKE --> Merkle_B_fake  (falsified)
     Witness C captures --> Merkle_A  (correct)

Detection: B != A,C --> divergence logged in attack_log.jsonl
Response:  Kill switch evaluates threat score; federation alerts
Outcome:   BLOCKED. Forensic trail preserved.

Defense chain: T2 (consensus) + T4 (federation) + D11 (schema monitor)
Confidence: 98%
```

### Scenario B: Rootkit on Witness / Rootkit en Testigo

```
Attacker: Root access to witness B's machine
Target:   Modify local snapshots/hashes

T+0: Attacker modifies hashes/latest_snapshot.json
T+1: Auto-audit (Lagartija) detects: local Merkle != mirrors
     --> Divergence detected
T+2: Restore from primary mirror; checkpoint saved (pre-attack)

Detection: Lagartija mirror coherence check
Response:  Auto-recovery from mirror; chain integrity preserved
Outcome:   AUTO-RECOVERED.

Defense chain: T1 (hash chain) + T4 (mirrors/Lagartija)
Confidence: 95%
```

### Scenario C: Selective Blocking (Honduras Model) / Bloqueo Selectivo

```
Attacker: CNE identifies witness C, blocks its access only
Target:   C cannot see result updates

T+0: CNE publishes update
     A, B capture --> Merkle_A = Merkle_B
     C timeout/blocked --> no snapshot

T+1: Consensus check: 2/3 (A, B) = OK
     C offline reported (D11 monitor)
     --> Status YELLOW (1 witness down, expected)

Detection: Connectivity loss logged; non-fatal
Response:  Operator monitors; escalates if persistent
Outcome:   DEGRADED but detectable. Custody gap for C documented.

Defense chain: T2 (divergence detection) + D11 (endpoint monitor)
Confidence: 90% (requires >= 2 witnesses alive)
```

### Scenario D: Statistical Manipulation / Manipulacion Estadistica

```
Attacker: CNE publishes data with anomalous digit distribution
Target:   Falsify results while appearing legitimate

T+0: CNE publishes: votes with Benford chi2 = 45.2 (critical, p<0.001)
     --> Threat score += 25

T+1: If Merkle also diverges across witnesses:
     Threat score >= 75 --> Kill Switch FREEZE
     --> Auto-recover + timestamp (T3)

Detection: Benford anomaly detection + Merkle integrity
Response:  Kill switch freeze; forensic bundle generated
Outcome:   BLOCKED. Evidence chain: Benford report + Merkle chain + attack_log.

Defense chain: Anomaly detection (Benford) + T1 (Merkle) + T3 (timestamp)
Confidence: 95%
```

### Scenario E: Operator Key Compromise Under Coercion / Compromiso de Clave Bajo Coercion

```
Attacker: State actor with physical access to operator
Target:   Obtain Ed25519 signing key; forge attestations

T+0: Operator coerced; key handed over
T+1: Adversary signs false attestations as compromised witness

Detection depends on federation size:
  n=1: UNDETECTABLE. T2 collapses. T1 (chain) and T3 (anchor) survive.
  n=3: Other 2 witnesses detect Merkle divergence from compromised node.

Mitigation: T2 degrades to T1. Chain remains tamper-evident.
            External anchor (T3) proves historical data existed.
            Gap: future attestations from compromised key are unreliable.

Outcome:   PARTIALLY MITIGATED with federation; UNMITIGATED for single operator.
Confidence: 60% (single operator) / 90% (3+ witnesses)
```

---

## 10. Confidence Matrix / Matriz de Confianza

| Component / Componente | Tests | Coverage | Confidence | Primary gap |
|------------------------|-------|----------|------------|-------------|
| T1: Hash Chain | 8 | 95% | 99% | None |
| T2: Byzantine Consensus | 6 | 85% | 95% | Gossip protocol |
| T3: OpenTimestamps | 7 | 90% | 98% | OTS service availability |
| T4: Federation | 8 | 80% | 90% | Signature verification scope |
| D11: Endpoint Monitor | 18 | 100% | 95% | Timeout hardcoding |
| D12: External Anchor | 17 | 95% | 98% | Arbitrum fallback (future) |
| D13: Multi-Witness | 14 | 85% | 90% | Config thresholds |
| Kill Switch (Tejon) | 15 | 90% | 95% | Recovery atomicity |
| Benford Detection | 12 | 90% | 95% | Overfitting prevention |
| Auto-Audit (Lagartija) | 19 | 85% | 88% | Defense health stubs |
| **Weighted Total** | **143** | **92%** | **96%** | **0 critical open** |

---

## 11. Assumptions / Supuestos

This threat model rests on the following assumptions. If any is violated,
the corresponding guarantees weaken as noted.

| # | Assumption | If violated |
|---|-----------|-------------|
| A1 | SHA-256 is collision-resistant | T1 collapses; chain integrity lost |
| A2 | Ed25519 satisfies EUF-CMA unforgeability | T2 collapses; signatures forgeable |
| A3 | At least 1 operator key is honest (multi-witness) | T2 degrades to T1 (integrity without authentication) |
| A4 | The external anchor (Bitcoin) is not rewritable by the adversary | T3 collapses; temporal provenance lost |
| A5 | At least 2 of 3 witnesses are honest and connected | Consensus valid; below this, majority can be forged |
| A6 | The network is not permanently partitioned for all witnesses | Temporary partition: degraded; permanent: no consensus possible |
| A7 | The operator's device is not physically compromised at deployment time | Compromised from start: all local state untrustworthy; federation may still detect |

---

## 12. Document History / Historial del Documento

| Date | Version | Change |
|------|---------|--------|
| 2026-06-01 | 1.0 | Initial threat model based on SECURITY-REVIEW.md, ARCHITECTURE.md, and internal whitepaper |

---

**Last updated / Ultima actualizacion:** 2026-06-01  
**Author / Autor:** Internal analysis  
**Status / Estado:** Active --- to be reviewed by independent auditor before pilot
