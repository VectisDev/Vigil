# CENTINEL — Pre-Capture Evidentiary Custody Model
# Modelo de Custodia de Evidencia Pre-Captura

**Audit finding addressed:** Point 1 — Pre-capture custody gap.
**Hallazgo de auditoría:** Punto 1 — Brecha de custodia pre-captura.

---

## 1. The problem / El problema

CENTINEL's hash chain provides strong tamper-evidence for captured data
**after** it enters the system. But it currently cannot answer a critical
evidentiary question: **how do we prove the JSON came from the CNE server
and not from our own software?**

La cadena de hashes de CENTINEL provee fuerte evidencia anti-tampering
para los datos capturados **después** de que entran al sistema. Pero
actualmente no puede responder una pregunta crítica de evidencia: **¿cómo
probamos que el JSON vino del servidor del CNE y no de nuestro propio
software?**

Specifically, the following challenges remain open in the current architecture:

Específicamente, los siguientes desafíos permanecen abiertos:

| Challenge | Without pre-capture custody | With pre-capture custody |
|-----------|----------------------------|--------------------------|
| "You fabricated those JSONs" | No direct counter-evidence | TLS fingerprint + IP + server Date header, verifiable against CT logs and passive DNS |
| "You modified the JSON after capture" | Hash chain only proves chain integrity, not provenance | Body hash computed on raw bytes BEFORE any parsing; included in Ed25519-signed envelope |
| "Your capture software was compromised" | No way to distinguish | Multi-operator federation (separate work); envelope signed by long-term key from air-gapped ceremony |
| "The timestamp is wrong" | Only system clock | Server's own `Date:` header is captured and signed |

| Desafío | Sin custodia pre-captura | Con custodia pre-captura |
|---------|--------------------------|--------------------------|
| "Fabricaste esos JSONs" | Sin contra-evidencia directa | TLS fingerprint + IP + header Date del servidor, verificables contra CT logs y passive DNS |
| "Modificaste el JSON después de capturarlo" | El hash chain solo prueba integridad de cadena, no procedencia | Hash del body en bytes crudos ANTES de cualquier parseo; incluido en sobre firmado por Ed25519 |
| "Tu software de captura fue comprometido" | Sin forma de distinguir | Federación multi-operador (trabajo separado); sobre firmado por clave de largo plazo desde ceremonia air-gapped |
| "La marca temporal está equivocada" | Solo reloj del sistema | El propio header `Date:` del servidor es capturado y firmado |

---

## 2. How the envelope works / Cómo funciona el sobre

For each CNE JSON capture, the system now produces a `CustodyEnvelope`
**before** parsing the JSON, applying any statistical rule, or extending
the hash chain.

Para cada captura de JSON del CNE, el sistema ahora produce un
`CustodyEnvelope` **antes** de parsear el JSON, aplicar reglas
estadísticas, o extender el hash chain.

```
                                 CNE server
                                     │
                              HTTP GET request
                                     │
                           ┌─────────▼──────────┐
                           │  1. TLS metadata   │  ◄── IP, cert SHA-256,
                           │     extracted      │      tls_version, cipher
                           └─────────┬──────────┘
                                     │
                           ┌─────────▼──────────┐
                           │  2. Raw body bytes │  ◄── SHA-256 computed
                           │     captured       │      on wire bytes
                           └─────────┬──────────┘
                                     │
                           ┌─────────▼──────────┐
                           │  3. CustodyEnvelope│  ◄── All evidence
                           │     constructed    │      bundled
                           └─────────┬──────────┘
                                     │
                           ┌─────────▼──────────┐
                           │  4. Signed by      │  ◄── Ed25519, from
                           │     operator key   │      air-gapped ceremony
                           └─────────┬──────────┘
                                     │
                      ┌──────────────▼───────────────────┐
                      │  5. Hash chain link created      │  ◄── prev hash +
                      │     (includes envelope hash)     │      envelope hash
                      └──────────────┬───────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  6. JSON parsed and │
                          │     rules applied   │
                          └─────────────────────┘
```

Steps 1–4 happen **before** step 6. The envelope is part of the hash
chain link (step 5), so any subsequent alteration of the envelope or the
JSON it attests to is detectable by verifying the chain.

Los pasos 1–4 ocurren **antes** del paso 6. El sobre es parte del
eslabón del hash chain (paso 5), por lo que cualquier alteración
posterior del sobre o del JSON que atestigua es detectable verificando
la cadena.

---

## 3. Integration with the existing poller / Integración con el poller existente

The module is designed to wrap the existing HTTP fetch in `poller.py`
with minimal changes. The integration point is the layer between
"bytes received from network" and "JSON handed to rules engine."

El módulo está diseñado para envolver el fetch HTTP existente en
`poller.py` con cambios mínimos. El punto de integración es la capa
entre "bytes recibidos de la red" y "JSON entregado al motor de reglas."

### Minimal integration snippet / Fragmento mínimo de integración

```python
# In src/centinel/core/poller.py — minimal integration
# En src/centinel/core/poller.py — integración mínima

import urllib.request
from centinel.core.pre_capture_custody import (
    build_envelope,
    sign_envelope,
    extract_tls_metadata,
    envelope_sha256,
)

def fetch_snapshot(url: str, operator_id: str, operator_private_key, prev_link: str):
    """
    Fetch a CNE snapshot URL, build a custody envelope, sign it,
    and return (raw_bytes, custody_envelope) before any parsing.

    Descarga una URL de snapshot del CNE, construye un sobre de
    custodia, lo firma y retorna (raw_bytes, custody_envelope)
    antes de cualquier parseo.
    """
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or 443

    # Step 1: Extract TLS metadata BEFORE the HTTP fetch.
    # Paso 1: Extraer metadata TLS ANTES del fetch HTTP.
    tls_meta = extract_tls_metadata(hostname, port)

    # Step 2: Fetch the URL, keeping raw bytes.
    # Paso 2: Descargar la URL, conservando los bytes crudos.
    req = urllib.request.Request(url, headers={"User-Agent": "centinel/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw_body = resp.read()
        status = resp.status
        headers = dict(resp.headers)

    # Step 3: Build the envelope over raw bytes (pre-parse).
    # Paso 3: Construir el sobre sobre los bytes crudos (pre-parseo).
    envelope = build_envelope(
        url=url,
        operator_id=operator_id,
        response_body=raw_body,
        response_status=status,
        response_headers=headers,
        tls_metadata=tls_meta,
        previous_chain_link_sha256=prev_link,
    )

    # Step 4: Sign the envelope.
    # Paso 4: Firmar el sobre.
    signed_envelope = sign_envelope(envelope, operator_private_key)

    # Step 5: Compute the hash of the signed envelope — this becomes
    # the "prev_link" for the next capture.
    # Paso 5: Computar el hash del sobre firmado — se convierte en
    # el "prev_link" de la siguiente captura.
    chain_link = envelope_sha256(signed_envelope)

    return raw_body, signed_envelope, chain_link

    # Step 6: Only AFTER the above, parse the JSON and run rules.
    # Paso 6: Solo DESPUÉS de lo anterior, parsear JSON y ejecutar reglas.
    # import json
    # snapshot = json.loads(raw_body)
    # rules_engine.run(snapshot)
```

### What to store / Qué almacenar

Each envelope should be persisted alongside the JSON snapshot:

Cada sobre debe persistirse junto al snapshot JSON:

```
data/
  snapshots/
    hnd_2025/
      snapshot_001.json           ← parsed CNE data
      snapshot_001.envelope.json  ← custody envelope (signed)
      snapshot_001.chain_link     ← sha256 of envelope (link to next)
```

The envelope JSON can be stored with `json.dumps(envelope.to_dict(), indent=2)`.
It is safe to publish — it contains no private key material.

El JSON del sobre se puede almacenar con `json.dumps(envelope.to_dict(), indent=2)`.
Es seguro publicar — no contiene material de clave privada.

---

## 4. What each field proves / Qué prueba cada campo

| Field | Evidence it provides |
|-------|---------------------|
| `url_requested` | The exact URL that was polled |
| `host_resolved_ip` | The IP address the DNS resolved to at capture time; verifiable against passive DNS records |
| `tls_cert_sha256_der` | The leaf certificate served at capture time; verifiable against Certificate Transparency logs (crt.sh, Google CT) |
| `tls_cert_not_before/after_utc` | Certificate validity window; proves the cert existed at the claimed time |
| `server_date_header` | The CNE server's own clock at time of response |
| `response_body_sha256` | SHA-256 of raw bytes before any parsing; any alteration changes this hash |
| `previous_chain_link_sha256` | Links this envelope into the temporal chain of all prior captures |
| `operator_signature_ed25519_hex` | Proves the envelope was assembled by an operator whose key was established in a documented air-gapped ceremony |

| Campo | Evidencia que provee |
|-------|---------------------|
| `url_requested` | La URL exacta que fue consultada |
| `host_resolved_ip` | La IP que el DNS resolvió al momento de captura; verificable contra registros de passive DNS |
| `tls_cert_sha256_der` | El certificado hoja servido al momento de captura; verificable contra logs de Certificate Transparency (crt.sh, Google CT) |
| `tls_cert_not_before/after_utc` | Ventana de validez del certificado; prueba que el certificado existía al momento reclamado |
| `server_date_header` | El reloj propio del servidor CNE al momento de la respuesta |
| `response_body_sha256` | SHA-256 de bytes crudos antes de cualquier parseo; cualquier alteración cambia este hash |
| `previous_chain_link_sha256` | Enlaza este sobre en la cadena temporal de todas las capturas previas |
| `operator_signature_ed25519_hex` | Prueba que el sobre fue ensamblado por un operador cuya clave fue establecida en una ceremonia air-gapped documentada |

---

## 5. Independent verification procedure / Procedimiento de verificación independiente

Any third party can verify an envelope without access to CENTINEL's code:

Cualquier tercero puede verificar un sobre sin acceso al código de CENTINEL:

```python
import json, hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Load envelope / Cargar sobre
envelope = json.load(open("snapshot_001.envelope.json"))

# 1. Verify body hash / Verificar hash del body
raw_body = open("snapshot_001.json", "rb").read()
assert hashlib.sha256(raw_body).hexdigest() == envelope["response_body_sha256"], \
    "Body hash mismatch — JSON was altered after capture"

# 2. Verify TLS cert against CT log (manual step)
# curl "https://crt.sh/?sha256=<tls_cert_sha256_der>&output=json"
# Should return a certificate issued before the capture time.

# 3. Verify Ed25519 signature
# Reconstruct canonical bytes
sig_fields = {
    "operator_signature_ed25519_hex",
    "operator_public_key_ed25519_hex",
}
canonical = json.dumps(
    {k: v for k, v in sorted(envelope.items()) if k not in sig_fields},
    sort_keys=True, separators=(",", ":"), ensure_ascii=False
).encode("utf-8")

pub_bytes = bytes.fromhex(envelope["operator_public_key_ed25519_hex"])
signature = bytes.fromhex(envelope["operator_signature_ed25519_hex"])
pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
pub_key.verify(signature, canonical)  # Raises InvalidSignature if wrong
print("✓ All checks passed")
```

This verification uses only the Python standard library plus `cryptography`
— no CENTINEL code is required. This is intentional: observers who distrust
CENTINEL's code can verify independently.

Esta verificación usa solo la librería estándar de Python más `cryptography`
— no se requiere código de CENTINEL. Esto es intencional: observadores que
desconfíen del código de CENTINEL pueden verificar de forma independiente.

---

## 6. Limitations / Limitaciones

1. **TLS cert ≠ CNE identity.** A TLS certificate issued for `cne.hn` by
   a trusted CA proves DNS ownership at issuance time, not that the
   server content was authoritative. A compromised DNS resolver could
   point `cne.hn` to an adversary's server with a valid cert. Mitigation:
   cross-referencing the IP against known CNE netblocks and requiring
   consistency across federation nodes (planned separate work).

2. **Server `Date:` header is advisory.** The CNE server controls its
   own clock. A compromised or misconfigured server could serve a wrong
   date. Mitigation: OpenTimestamps anchoring of the chain root provides
   an external lower-bound timestamp independent of the server.

3. **TLS chain is leaf-only in the current implementation.** The full
   certificate chain (intermediate CAs) is not extracted. This reduces
   the depth of CT log verification. Planned: integrate `cryptography.x509`
   to extract the full chain DER-by-DER.

4. **This module handles network-reachable captures only.** The HN 2025
   retroactive analysis used manually downloaded files — those captures
   have no TLS envelope because the capture happened manually. This
   limitation is documented in the methodology section.

---

## 7. File path for integration / Ruta de archivo para integración

Place in the CENTINEL repository at:

Colocar en el repositorio CENTINEL en:

```
src/centinel/core/pre_capture_custody.py   ← the module
tests/test_pre_capture_custody.py          ← its test suite
docs/architecture/PRE-CAPTURE-CUSTODY-MODEL.md ← this document
```

Add to `pyproject.toml` dependencies (already present):
```
cryptography>=42.0.0
```
