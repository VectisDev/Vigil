# CENTINEL — Key Ceremony Protocol v1.0
# Protocolo de Ceremonia de Claves de CENTINEL v1.0

**Audit finding addressed:** Point 6 — Bus factor = 1 (Lone Developer Risk).
**Severity:** 🔴 CRITICAL.
**Document classification:** PUBLIC after redaction of custodian travel details.

**Hallazgo de auditoría que aborda:** Punto 6 — Bus factor = 1 (Riesgo de
desarrollador único).
**Severidad:** 🔴 CRÍTICO.
**Clasificación del documento:** PÚBLICO tras redacción de detalles de
desplazamiento de custodios.

---

## 1. Purpose / Propósito

This protocol establishes the procedure for generating, splitting, and
distributing the cryptographic signing keys used by CENTINEL to attest to
electoral evidence captures. The scheme uses Shamir Secret Sharing over
GF(2⁸) to divide each Ed25519 private key into `n` shares, of which any
`k` are sufficient to reconstruct the key.

Este protocolo establece el procedimiento para generar, dividir y
distribuir las claves criptográficas de firma utilizadas por CENTINEL para
atestar las capturas de evidencia electoral. El esquema usa Shamir Secret
Sharing sobre GF(2⁸) para dividir cada clave privada Ed25519 en `n` shares,
de los cuales `k` cualesquiera son suficientes para reconstruir la clave.

## 2. Scheme parameters / Parámetros del esquema

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Threshold `k` | **3** | Sufficient redundancy: any 2 custodians being unavailable simultaneously does not block reconstruction. Below 3 would risk easy coercion of a single custodian. |
| Total shares `n` | **5** | Threshold/total ratio of 3/5 = 60% provides high resilience while keeping coordination feasible. |
| Field | GF(2⁸) / 0x11b | AES irreducible polynomial — well-studied, library implementations available for independent verification. |
| Key type | Ed25519 | Used throughout the CENTINEL codebase; 32-byte private keys; constant-time signing. |
| Format | ASCII-armored, base64 | Printable on paper; can be sent over text channels; integrity-checked by SHA-256. |

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| Umbral `k` | **3** | Redundancia suficiente: que 2 custodios estén indisponibles simultáneamente no bloquea la reconstrucción. Menos de 3 facilitaría la coacción de un solo custodio. |
| Shares totales `n` | **5** | Ratio umbral/total 3/5 = 60% provee alta resiliencia manteniendo la coordinación factible. |
| Campo | GF(2⁸) / 0x11b | Polinomio irreducible de AES — bien estudiado, implementaciones de librería existen para verificación independiente. |
| Tipo de clave | Ed25519 | Usado en todo el código CENTINEL; claves privadas de 32 bytes; firma de tiempo constante. |
| Formato | ASCII-armored, base64 | Imprimible en papel; enviable por canales de texto; integridad verificada por SHA-256. |

## 3. Custodians / Custodios

The custodian roster MUST satisfy:

El listado de custodios DEBE satisfacer:

1. **Geographic distribution.** At least 2 custodians in jurisdictions
   distinct from Honduras. This frustrates any single-jurisdiction
   coercion attempt.

   Al menos 2 custodios en jurisdicciones distintas a Honduras. Esto
   frustra cualquier intento de coacción desde una sola jurisdicción.

2. **Institutional diversity.** No more than 2 custodians from the same
   institution, family, or political affiliation.

   No más de 2 custodios de la misma institución, familia o filiación
   política.

3. **Operational competence.** All custodians MUST be able to:
   - Securely store a printed share for at least 5 years.
   - Re-key the share into a computer (or transmit to a trusted
     reconstruction operator) when called upon.
   - Refuse to disclose the share to any party, including the project
     itself, except in a documented reconstruction event.

   Todos los custodios DEBEN poder:
   - Almacenar de forma segura un share impreso por al menos 5 años.
   - Re-ingresar el share en un computador (o transmitirlo a un operador
     de reconstrucción de confianza) cuando se les solicite.
   - Negarse a divulgar el share a cualquier parte, incluido el propio
     proyecto, excepto en un evento documentado de reconstrucción.

### Suggested custodian assignment / Asignación sugerida de custodios

| # | Custodian | Role | Jurisdiction |
|---|-----------|------|--------------|
| 1 | Carlos Zelaya | Primary operator | Honduras |
| 2 | Prof. Devis Alvarado | Academic validator (UPNFM) | Honduras |
| 3 | Ing. Mario Roberto Zelaya Guzmán | Fiscal custodian (IGETEL) | Honduras |
| 4 | TBD | Independent custodian | Mexico / Costa Rica / Spain |
| 5 | TBD | Independent custodian | Different jurisdiction from #4 |

> **Note on conflict of interest:** Custodians #1 and #3 have a familial
> relationship. This is disclosed publicly. Because reconstruction
> requires `k=3` of `n=5` shares, no two custodians (related or otherwise)
> can reconstruct alone — at least one independent custodian (#2, #4, or
> #5) must participate in any reconstruction.

> **Nota sobre conflicto de interés:** Los custodios #1 y #3 tienen una
> relación familiar. Esto se divulga públicamente. Como la reconstrucción
> requiere `k=3` de `n=5` shares, dos custodios cualesquiera (relacionados
> o no) no pueden reconstruir solos — al menos un custodio independiente
> (#2, #4 o #5) debe participar en cualquier reconstrucción.

## 4. Ceremony pre-requisites / Pre-requisitos de la ceremonia

### Hardware

- **Air-gapped machine.** A computer that has never connected to a network
  and never will, or a laptop with Wi-Fi/Bluetooth physically disabled and
  Ethernet unplugged.
- **Tails OS USB** (recommended) or a freshly imaged Linux distribution
  from verified ISO checksums.
- **Printer** within physical line of sight of all custodians during
  printing (no networked printer; no shared office printer).
- **Paper envelopes**, one per custodian, labeled and signed across the
  seal by all 5 custodians.

### Hardware (español)

- **Máquina air-gapped.** Un computador que jamás ha conectado a una red
  y nunca lo hará, o una laptop con Wi-Fi/Bluetooth físicamente
  deshabilitados y Ethernet desconectado.
- **USB con Tails OS** (recomendado) o una distro Linux recién creada
  desde checksums ISO verificados.
- **Impresora** a la vista física de todos los custodios durante la
  impresión (no impresora de red; no impresora de oficina compartida).
- **Sobres de papel**, uno por custodio, etiquetados y firmados sobre el
  sello por los 5 custodios.

### Software

- Python 3.11+ with `cryptography` library installed offline.
- The four CENTINEL ceremony scripts (`centinel_shamir.py`,
  `centinel_share_format.py`, `centinel_key_ceremony.py`,
  `centinel_key_reconstruct.py`).
- The full test suite (`test_key_ceremony.py`) run successfully on the
  air-gapped machine before the ceremony.

### Procedural

- All 5 custodians physically present.
- An independent witness (recommended: a notary public, an attorney, or
  a senior academic outside the project) to observe and sign the
  ceremony record.
- A pre-printed paper checklist of the protocol steps to be initialed by
  the operator after each completed step.

## 5. Ceremony procedure / Procedimiento de la ceremonia

### Phase A — Setup verification (15 min)

```
[ ] A.1  Verify physical setting: room secure, no recording devices,
         no networked equipment beyond the offline laptop.
[ ] A.2  Verify all 5 custodians present and identified.
[ ] A.3  Run pytest on the ceremony machine to confirm all 47 tests pass.
         > pytest tests/test_key_ceremony.py -v
[ ] A.4  Verify date/time on the offline machine is reasonably accurate
         (within a few minutes — does not need to be precise).
[ ] A.5  Confirm network is disconnected.
[ ] A.6  Witness signs Phase A as observed.
```

### Phase B — Key generation (10 min)

```
[ ] B.1  Operator executes:
         > python centinel_key_ceremony.py \
             --custodians "Name1,Name2,Name3,Name4,Name5" \
             --threshold 3 \
             --output-dir ./ceremony-output \
             --key-name witness_<year>

[ ] B.2  Operator reads the displayed public key and SHA-256 aloud.
         All custodians visually confirm.

[ ] B.3  Operator types "yes" to confirm.

[ ] B.4  Verify 7 files were created:
         - witness_<year>.public_key
         - witness_<year>.ceremony_record.json
         - witness_<year>.share_01.txt through share_05.txt

[ ] B.5  Witness signs Phase B as observed.
```

### Phase C — Share distribution (20 min)

```
[ ] C.1  For each share file (1 through 5):
         a) Print the share file (and only that share file).
         b) Hand the printed share to its designated custodian.
         c) The custodian visually verifies the "Custodian:" header
            matches their name.
         d) The custodian seals the share in their envelope.
         e) The custodian initials the ceremony record next to their
            share's hash.

[ ] C.2  Operator verifies the printed shares match the on-screen output.
         (Compare the first/last 8 characters of base64 visually.)

[ ] C.3  Witness signs Phase C as observed.
```

### Phase D — Verification test (15 min)

```
[ ] D.1  Three randomly-chosen custodians temporarily re-enter their
         shares into the offline machine for reconstruction test.
         > python centinel_key_reconstruct.py \
             --share share_X.txt --share share_Y.txt --share share_Z.txt \
             --expected-public-key witness_<year>.public_key \
             --print-public-key

[ ] D.2  Verify the output reads:
         "Reconstruction successful.
            - Verified against declared secret hash ✓
            - Verified against expected public key ✓"

[ ] D.3  Custodians retrieve their (still-sealed) envelopes.

[ ] D.4  Witness signs Phase D as observed.
```

### Phase E — Wipe and finalization (10 min)

```
[ ] E.1  Securely wipe ALL files from the ceremony machine:
         > shred -u -n 7 ./ceremony-output/*.txt
         > shred -u -n 7 ./ceremony-output/*.json (will be republished)
         > rm -rf ./ceremony-output/

[ ] E.2  Power off the offline machine. Remove its hard drive (if
         removable) and physically destroy it, OR wipe the entire disk
         with `dd if=/dev/urandom of=/dev/sdX bs=1M`.

[ ] E.3  Print and sign the final ceremony record. The signed PDF version
         will be:
           - Anchored to OpenTimestamps after the ceremony
           - Published to the CENTINEL repository
           - Stored by each custodian alongside their share envelope

[ ] E.4  Witness signs Phase E as observed.
[ ] E.5  All custodians sign the ceremony record.
[ ] E.6  Operator declares the ceremony concluded.
```

## 6. Reconstruction events / Eventos de reconstrucción

Reconstruction MUST only occur when:

La reconstrucción SOLO debe ocurrir cuando:

1. The primary operator is unable to continue operations and a new
   operator must be empowered with the signing key.
2. A scheduled key rotation (every 3 years, or after suspected
   compromise of operational infrastructure).
3. An emergency requires emergency signing for which the primary
   operator's individual key is unavailable.

Every reconstruction event MUST be:

Todo evento de reconstrucción DEBE:

- Documented in writing with reasons, participants, and witnesses.
- Performed under the same offline conditions as the original ceremony.
- Followed by a new ceremony to generate a fresh key, with the
  reconstructed key revoked and burned.
- Reported publicly in the project's transparency log within 30 days
  of the event (excluding sensitive operational details about
  custodian identities or whereabouts when their safety is at issue).

## 7. Threat model & residual risks / Modelo de amenazas y riesgos residuales

### Threats addressed / Amenazas abordadas

| Threat | Mitigation |
|--------|-----------|
| Single operator compromised | 3-of-5 threshold; no single custodian can recover. |
| Single custodian compromised | Threshold requires 3, so 1 share compromised reveals no information. |
| Two custodians compromised | Same — 2 shares still reveal no information. |
| Lost share | 2 shares can be lost without preventing reconstruction. |
| Forged share submitted in reconstruction | SHA-256 of original secret is in every share; reconstruction verifies against this hash. |
| Custodian forgets which share is theirs | The Custodian header in each share file documents this. |

### Residual risks / Riesgos residuales

| Risk | Severity | Acceptance rationale |
|------|----------|----------------------|
| Coercion of 3+ custodians simultaneously | Low probability if jurisdictional diversity is maintained. | Trade-off with operational feasibility; raising threshold to 4-of-5 would block reconstruction if any 2 custodians are unavailable. |
| Ceremony machine compromised (firmware implant) | Low probability with Tails or freshly-imaged Linux. | Air-gap + physical destruction of disk after ceremony reduces this further. |
| Custodian deliberate betrayal | Mitigated by threshold > 1, public commitment, and legal liability under participation agreement. | Acceptable for current project scale. |
| Side-channel attack on Shamir math | None known for Lagrange interpolation in GF(2⁸) when computed via table lookup. | Implementation uses constant-time table lookup. |
| Quantum computer breaking Ed25519 | Theoretical only as of 2026; would compromise signing but not Shamir reconstruction itself. | Plan: rotate to post-quantum signing when NIST-standardized algorithms (CRYSTALS-Dilithium) are mature in target jurisdictions. |

## 8. Audit trail / Pista de auditoría

The following artifacts of each ceremony are published publicly:

Los siguientes artefactos de cada ceremonia se publican públicamente:

1. The `ceremony_record.json` file (no secret material).
2. The `public_key` file.
3. A scanned PDF of the signed paper ceremony record.
4. An OpenTimestamps proof anchoring (1)-(3) to Bitcoin.

The following are NEVER published or transmitted electronically:

Lo siguiente NUNCA se publica ni se transmite electrónicamente:

1. Any individual share.
2. The reconstructed private key.
3. The Shamir polynomial coefficients used during ceremony.

## 9. Schedule for first ceremony / Calendario para la primera ceremonia

| Date | Milestone |
|------|-----------|
| Within 2 weeks | Confirm 5 custodians; obtain commitment letters. |
| Within 4 weeks | Schedule ceremony date with all 5 custodians + witness. |
| Within 6 weeks | **First key ceremony executed.** |
| Within 7 weeks | Ceremony record OpenTimestamps-anchored and published. |

| Fecha | Hito |
|-------|------|
| En 2 semanas | Confirmar 5 custodios; obtener cartas de compromiso. |
| En 4 semanas | Programar fecha de la ceremonia con los 5 custodios + testigo. |
| En 6 semanas | **Primera ceremonia de claves ejecutada.** |
| En 7 semanas | Registro de ceremonia anclado a OpenTimestamps y publicado. |

## 10. References / Referencias

- Shamir, A. (1979). *How to share a secret.* Communications of the ACM,
  22(11), 612–613. doi:10.1145/359168.359176
- FIPS 197 — Advanced Encryption Standard (the choice of GF(2⁸) and
  irreducible polynomial 0x11b).
- NIST SP 800-90A — Recommendation for Random Number Generation
  (`secrets` module under the hood).
- RFC 8032 — Edwards-Curve Digital Signature Algorithm (Ed25519).
- Centinel internal: `docs/security/THREAT_MODEL.md`.

## 11. Document control / Control del documento

- **Version:** 1.0
- **Status:** Approved by red-team audit council, June 2026
- **Owner:** CENTINEL core maintainer
- **Review cadence:** Annually, plus after any reconstruction event
- **License:** AGPL-3.0 (matching the parent project)
