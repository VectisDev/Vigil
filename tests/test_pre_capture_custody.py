"""
CENTINEL — Test suite for the pre-capture custody module
=========================================================

Tests cover:
- Envelope construction from observed capture data
- Canonical serialization stability (same input → same bytes)
- SHA-256 envelope hashing
- Ed25519 sign/verify roundtrip
- Tamper detection: any post-signing modification invalidates the signature
- Body hash matches raw bytes (not parsed/decoded form)
- Expected-public-key cross-check
- Chain linking via previous_chain_link_sha256

Tests run without network access. A separate test file
``test_tls_metadata_live.py`` would be needed for live TLS extraction
tests against a real server, and is out of scope for the offline kit.

Run with:
    pytest tests/test_pre_capture_custody.py -v
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

# Package import with fallback for isolated test execution.
# Importación de paquete con fallback para ejecución aislada de tests.
try:
    from centinel.core.pre_capture_custody import (
        CustodyEnvelope, CustodyError, build_envelope,
        envelope_canonical_bytes, envelope_sha256,
        sign_envelope, verify_envelope,
    )
except ModuleNotFoundError:
    SRC_DIR = Path(__file__).resolve().parent.parent / "src"
    sys.path.insert(0, str(SRC_DIR))
    from pre_capture_custody import (  # type: ignore[no-redef]
        CustodyEnvelope, CustodyError, build_envelope,
        envelope_canonical_bytes, envelope_sha256,
        sign_envelope, verify_envelope,
    )

# Try to import cryptography; some tests are skipped if unavailable.
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ---------------------------------------------------------------------------
# Fixtures / Datos de prueba
# ---------------------------------------------------------------------------


SAMPLE_BODY = b'{"election":"HND-2025","status":"published","actas":15842}'

SAMPLE_HEADERS = {
    "Date": "Wed, 04 Dec 2025 18:30:42 GMT",
    "Content-Type": "application/json; charset=utf-8",
    "ETag": '"a1b2c3d4-1024"',
    "Last-Modified": "Wed, 04 Dec 2025 18:00:00 GMT",
    "Cache-Control": "no-cache",
    "Server": "nginx/1.24.0",
    "Content-Length": str(len(SAMPLE_BODY)),
}

SAMPLE_TLS = {
    "host_resolved_ip": "200.55.144.10",
    "tls_version": "TLSv1.3",
    "tls_cipher": "TLS_AES_256_GCM_SHA384",
    "tls_cert_subject": "CN=cne.hn",
    "tls_cert_issuer": "CN=DigiCert TLS RSA SHA256 2020 CA1, O=DigiCert Inc, C=US",
    "tls_cert_not_before_utc": "2025-08-01T00:00:00Z",
    "tls_cert_not_after_utc": "2026-09-01T23:59:59Z",
    "tls_cert_sha256_der": "f" * 64,
    "tls_cert_chain_sha256_der": ["f" * 64],
}


def make_envelope(captured_at_utc: str = "2025-12-04T18:30:42Z") -> CustodyEnvelope:
    """Helper that produces a deterministic envelope for testing."""
    return build_envelope(
        url="https://cne.hn/api/elections/2025/results.json",
        operator_id="centinel-operator-vectisdev",
        response_body=SAMPLE_BODY,
        response_status=200,
        response_headers=SAMPLE_HEADERS,
        tls_metadata=SAMPLE_TLS,
        previous_chain_link_sha256="a" * 64,
        notes="HN 2025 retroactive capture",
        captured_at_utc=captured_at_utc,
    )


# ---------------------------------------------------------------------------
# Construction tests / Pruebas de construcción
# ---------------------------------------------------------------------------


class TestBuildEnvelope:
    def test_construction_smoke(self):
        env = make_envelope()
        assert env.envelope_version == "1.0"
        assert env.url_requested.startswith("https://cne.hn")
        assert env.http_status_code == 200
        assert env.response_body_size_bytes == len(SAMPLE_BODY)

    def test_body_hash_matches_raw_bytes(self):
        env = make_envelope()
        expected = hashlib.sha256(SAMPLE_BODY).hexdigest()
        assert env.response_body_sha256 == expected

    def test_body_hash_is_pre_parse(self):
        """
        The body hash must be computed on raw bytes — even if the body
        is parseable JSON, the hash is over the bytes, not the parsed form.
        El hash del body debe computarse sobre bytes crudos.
        """
        # Two semantically-equal JSON encodings with different whitespace.
        body_a = b'{"a":1,"b":2}'
        body_b = b'{"a": 1, "b": 2}'
        env_a = build_envelope(
            url="https://x.test/", operator_id="op", response_body=body_a,
            response_status=200, response_headers={}, tls_metadata=SAMPLE_TLS,
        )
        env_b = build_envelope(
            url="https://x.test/", operator_id="op", response_body=body_b,
            response_status=200, response_headers={}, tls_metadata=SAMPLE_TLS,
        )
        # The two bodies parse to the same JSON, but the hashes differ
        # because the bytes differ. This is the property we want.
        # Los dos bodies parsean igual, pero los hashes difieren porque
        # los bytes difieren. Es la propiedad que queremos.
        assert env_a.response_body_sha256 != env_b.response_body_sha256

    def test_server_headers_pinned(self):
        env = make_envelope()
        assert env.server_date_header == "Wed, 04 Dec 2025 18:30:42 GMT"
        assert env.server_etag == '"a1b2c3d4-1024"'
        assert env.server_last_modified == "Wed, 04 Dec 2025 18:00:00 GMT"
        assert env.server_content_type == "application/json; charset=utf-8"

    def test_case_insensitive_header_extraction(self):
        """Server headers must be extracted regardless of header-name casing."""
        env = build_envelope(
            url="https://x.test/", operator_id="op", response_body=b"x",
            response_status=200,
            response_headers={"DATE": "test", "ETAG": "weird-etag"},
            tls_metadata=SAMPLE_TLS,
        )
        assert env.server_date_header == "test"
        assert env.server_etag == "weird-etag"

    def test_tls_metadata_propagated(self):
        env = make_envelope()
        assert env.host_resolved_ip == "200.55.144.10"
        assert env.tls_version == "TLSv1.3"
        assert env.tls_cert_subject == "CN=cne.hn"
        assert env.tls_cert_sha256_der == "f" * 64

    def test_non_bytes_body_raises(self):
        with pytest.raises(CustodyError):
            build_envelope(
                url="https://x.test/", operator_id="op",
                response_body="not bytes",  # type: ignore
                response_status=200, response_headers={},
                tls_metadata=SAMPLE_TLS,
            )

    def test_each_envelope_has_unique_id(self):
        env1 = make_envelope()
        env2 = make_envelope()
        assert env1.envelope_id != env2.envelope_id


# ---------------------------------------------------------------------------
# Canonicalization tests / Pruebas de canonicalización
# ---------------------------------------------------------------------------


class TestCanonicalization:
    def test_canonical_bytes_is_deterministic_for_same_envelope(self):
        env = make_envelope()
        env.envelope_id = "fixed-id"  # Pin the random field for the test.
        a = envelope_canonical_bytes(env)
        b = envelope_canonical_bytes(env)
        assert a == b

    def test_canonical_excludes_signature_fields(self):
        """
        The canonical bytes must not depend on the signature fields,
        otherwise signing would be self-referential.
        Los bytes canónicos no deben depender de los campos de firma.
        """
        env = make_envelope()
        before = envelope_canonical_bytes(env)
        env.operator_signature_ed25519_hex = "deadbeef" * 16
        env.operator_public_key_ed25519_hex = "cafebabe" * 8
        after = envelope_canonical_bytes(env)
        assert before == after

    def test_canonical_uses_sorted_keys(self):
        env = make_envelope()
        env.envelope_id = "fixed-id"
        canonical = envelope_canonical_bytes(env)
        parsed = json.loads(canonical)
        # Verify keys are in sorted order in the actual bytes.
        # Verificar que las claves están ordenadas alfabéticamente.
        canonical_str = canonical.decode("utf-8")
        keys_in_order = [k for k in parsed.keys()]
        # JSON dicts preserve insertion order in Python 3.7+, and sort_keys
        # produces a sorted insertion. So keys_in_order == sorted(keys_in_order).
        assert keys_in_order == sorted(keys_in_order)

    def test_canonical_has_no_whitespace_between_tokens(self):
        env = make_envelope()
        canonical = envelope_canonical_bytes(env).decode("utf-8")
        # The separators argument removes the standard ", " and ": " whitespace.
        # But there CAN be whitespace inside string values (e.g., the Date header).
        # So we check by ensuring there are no " : " or " , " patterns.
        # Specifically, the separator between key and value should be ":" not ": "
        # and between elements should be "," not ", ".
        # Check: ":, " and ", \"" patterns should not exist outside strings.
        # Approximation: count separators.
        # Conteo aproximado de separadores.
        # The simpler invariant: the canonical form must be reproducible
        # from json.loads + json.dumps with the same args.
        # La forma canónica debe ser reproducible.
        d = json.loads(canonical)
        recanonical = json.dumps(
            d, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        assert canonical == recanonical

    def test_envelope_sha256_matches_canonical_hash(self):
        env = make_envelope()
        expected = hashlib.sha256(envelope_canonical_bytes(env)).hexdigest()
        assert envelope_sha256(env) == expected


# ---------------------------------------------------------------------------
# Signing tests / Pruebas de firma (require cryptography)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")
class TestSigning:
    def test_sign_and_verify_roundtrip(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key)
        assert signed.operator_signature_ed25519_hex != ""
        assert signed.operator_public_key_ed25519_hex != ""
        assert verify_envelope(signed) is True

    def test_signature_is_64_bytes(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key)
        # Ed25519 signatures are 64 bytes / 128 hex chars.
        # Firmas Ed25519 son 64 bytes / 128 chars hex.
        assert len(signed.operator_signature_ed25519_hex) == 128

    def test_public_key_is_32_bytes(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key)
        assert len(signed.operator_public_key_ed25519_hex) == 64

    def test_tampering_with_url_invalidates_signature(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key)
        # Modify URL after signing.
        # Modificar URL después de firmar.
        signed.url_requested = "https://evil.test/fake"
        assert verify_envelope(signed) is False

    def test_tampering_with_body_hash_invalidates_signature(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key)
        signed.response_body_sha256 = "0" * 64
        assert verify_envelope(signed) is False

    def test_tampering_with_status_invalidates_signature(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key)
        signed.http_status_code = 500
        assert verify_envelope(signed) is False

    def test_tampering_with_previous_chain_link_invalidates_signature(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key)
        signed.previous_chain_link_sha256 = "0" * 64
        assert verify_envelope(signed) is False

    def test_unsigned_envelope_does_not_verify(self):
        env = make_envelope()
        # No signing performed. / No se ha firmado.
        assert verify_envelope(env) is False

    def test_signature_with_wrong_key_does_not_verify(self):
        env = make_envelope()
        key1 = Ed25519PrivateKey.generate()
        key2 = Ed25519PrivateKey.generate()
        signed = sign_envelope(env, key1)
        # Replace the public key with one that doesn't match the signature.
        # Reemplazar la public key con una que no corresponde a la firma.
        wrong_pub = key2.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        signed.operator_public_key_ed25519_hex = wrong_pub.hex()
        assert verify_envelope(signed) is False

    def test_verify_with_expected_public_key_succeeds_when_correct(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        expected_pub = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        signed = sign_envelope(env, key)
        assert verify_envelope(signed, expected_public_key=expected_pub) is True

    def test_verify_with_expected_public_key_fails_on_mismatch(self):
        env = make_envelope()
        key = Ed25519PrivateKey.generate()
        other_key = Ed25519PrivateKey.generate()
        other_pub = other_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        signed = sign_envelope(env, key)
        # Signature is valid in itself, but does not match the expected pubkey.
        # La firma es válida en sí, pero no coincide con la pubkey esperada.
        assert verify_envelope(signed, expected_public_key=other_pub) is False

    def test_malformed_signature_hex_does_not_crash(self):
        env = make_envelope()
        env.operator_signature_ed25519_hex = "not-hex-XYZ"
        env.operator_public_key_ed25519_hex = "also-not-hex"
        # Should fail gracefully, not crash.
        # Debe fallar limpiamente, no crashearse.
        assert verify_envelope(env) is False


# ---------------------------------------------------------------------------
# Chain linking tests / Pruebas de encadenamiento
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")
class TestChainLinking:
    def test_two_envelopes_can_form_a_chain(self):
        """
        Demonstrate that envelope N+1 can reference envelope N's hash,
        creating a tamper-evident chain.
        """
        key = Ed25519PrivateKey.generate()

        # First envelope: no previous link.
        env_a = build_envelope(
            url="https://cne.hn/api/results/1.json",
            operator_id="op",
            response_body=b'{"snapshot":1}',
            response_status=200,
            response_headers={"Date": "Wed, 04 Dec 2025 18:00:00 GMT"},
            tls_metadata=SAMPLE_TLS,
            previous_chain_link_sha256="",
            captured_at_utc="2025-12-04T18:00:00Z",
        )
        signed_a = sign_envelope(env_a, key)
        link_a = envelope_sha256(signed_a)

        # Second envelope: references first.
        env_b = build_envelope(
            url="https://cne.hn/api/results/2.json",
            operator_id="op",
            response_body=b'{"snapshot":2}',
            response_status=200,
            response_headers={"Date": "Wed, 04 Dec 2025 18:30:00 GMT"},
            tls_metadata=SAMPLE_TLS,
            previous_chain_link_sha256=link_a,
            captured_at_utc="2025-12-04T18:30:00Z",
        )
        signed_b = sign_envelope(env_b, key)

        # Both verify independently.
        assert verify_envelope(signed_a) is True
        assert verify_envelope(signed_b) is True
        # Envelope B's previous_chain_link_sha256 equals A's hash.
        assert signed_b.previous_chain_link_sha256 == link_a

    def test_modifying_first_envelope_breaks_chain_continuity(self):
        """
        If someone alters envelope A after the fact, the recorded
        previous_chain_link_sha256 in envelope B no longer matches A's
        hash. We verify this property explicitly.
        """
        key = Ed25519PrivateKey.generate()

        env_a = build_envelope(
            url="https://cne.hn/api/results/1.json", operator_id="op",
            response_body=b'{"snapshot":1}', response_status=200,
            response_headers={}, tls_metadata=SAMPLE_TLS,
        )
        signed_a = sign_envelope(env_a, key)
        link_a = envelope_sha256(signed_a)

        env_b = build_envelope(
            url="https://cne.hn/api/results/2.json", operator_id="op",
            response_body=b'{"snapshot":2}', response_status=200,
            response_headers={}, tls_metadata=SAMPLE_TLS,
            previous_chain_link_sha256=link_a,
        )
        signed_b = sign_envelope(env_b, key)

        # Now an attacker modifies a non-signed field of A. The signature
        # of A breaks (caught by verify_envelope) but additionally the
        # chain link in B no longer matches A's recomputed hash.
        # Ahora un atacante modifica un campo de A. La firma de A se
        # rompe Y el chain link en B ya no corresponde al hash recomputado.
        signed_a.url_requested = "https://attacker.test/"

        assert verify_envelope(signed_a) is False  # Signature on A broken.

        # Recomputed hash of A no longer matches B's recorded link.
        # El hash recomputado de A ya no coincide con el link grabado en B.
        recomputed_link = envelope_sha256(signed_a)
        assert recomputed_link != signed_b.previous_chain_link_sha256
