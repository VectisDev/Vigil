"""
Tests for OpenTimestamps client.

Validates OTS integration, retry logic, and multi-chain fallback.
"""

import base64
import hashlib
import time
from unittest.mock import MagicMock, patch

import httpx

from vigil.anchor.opentimestamps_client import (
    MultichainAnchor,
    OpenTimestampsClient,
    TimestampProof,
)

# Cabecera magica real de un archivo .ots incompleto. El cliente solo mira los
# primeros bytes, pero la prueba usa la cabecera real para no afirmar nada
# sobre un formato inventado.
# English: real magic header of an incomplete .ots file. The client only reads
# the first bytes, but the fixture uses the genuine header so the test does not
# assert anything about a format that does not exist.
OTS_MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94\x01"
OTS_SAMPLE = OTS_MAGIC + b"\x08" + b"\xab" * 32


def _ots_response(content: bytes, status_code: int = 200) -> MagicMock:
    """Respuesta de una calendar: binario crudo, no JSON.

    English: a calendar server's response is raw binary, not JSON. The OTS REST
    protocol has no `ots_proof`/`bitcoin_tx` JSON body; `bitcoin_tx` is only
    known 1-24h later, after `ots upgrade`.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    return resp


class TestTimestampProof:
    """Test TimestampProof dataclass."""

    def test_create_proof(self):
        """Create valid timestamp proof."""
        proof = TimestampProof(
            timestamp=time.time(),
            message_hash="a" * 64,
            ots_response="abc123base64encoded",
            bitcoin_tx="abc123tx",
        )

        assert proof.message_hash == "a" * 64
        assert proof.bitcoin_tx == "abc123tx"
        assert proof.chain == "mainnet"
        assert proof.verified is False

    def test_proof_testnet(self):
        """Proof for testnet."""
        proof = TimestampProof(
            timestamp=time.time(),
            message_hash="b" * 64,
            ots_response="xyz789",
            chain="testnet",
        )

        assert proof.chain == "testnet"


class TestOpenTimestampsClient:
    """Test OpenTimestamps client."""

    def test_client_creation(self):
        """Create OTS client."""
        client = OpenTimestampsClient(timeout=10.0, max_retries=2)

        assert client.timeout == 10.0
        assert client.max_retries == 2
        assert client.use_testnet is False

    def test_client_testnet(self):
        """Create testnet OTS client."""
        client = OpenTimestampsClient(use_testnet=True)

        assert client.use_testnet is True
        assert len(client.servers) > 0

    def test_message_hash_from_string(self):
        """Hash message string."""
        import hashlib

        message = "checkpoint-2026-05-16T00:00:00Z"
        expected_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()

        # OTS client would compute this internally
        assert len(expected_hash) == 64

    def test_message_hash_from_bytes(self):
        """Hash message bytes."""
        import hashlib

        message = b"checkpoint-2026-05-16T00:00:00Z"
        expected_hash = hashlib.sha256(message).hexdigest()

        assert len(expected_hash) == 64

    @patch("httpx.Client.post")
    def test_stamp_success(self, mock_post):
        """stamp() devuelve el .ots binario en base64, sin datos de Bitcoin."""
        mock_post.return_value = _ots_response(OTS_SAMPLE)

        client = OpenTimestampsClient()
        proof = client.stamp("test message")

        assert proof is not None
        assert proof.message_hash == hashlib.sha256(b"test message").hexdigest()
        assert base64.b64decode(proof.ots_response) == OTS_SAMPLE

        # Una calendar NO devuelve transaccion ni bloque: la confirmacion llega
        # entre 1 y 24 h despues, via `ots upgrade`. Afirmar lo contrario daria
        # por anclado a Bitcoin algo que todavia no lo esta.
        # English: a calendar returns neither tx nor block; confirmation arrives
        # 1-24h later via `ots upgrade`. Asserting otherwise would report as
        # anchored to Bitcoin something that is not yet anchored.
        assert proof.bitcoin_tx is None
        assert proof.bitcoin_block is None
        assert proof.verified is False
        assert proof.chain == "mainnet"

        # El cuerpo enviado es el digest crudo de 32 bytes, no texto.
        _, kwargs = mock_post.call_args
        assert kwargs["content"] == bytes.fromhex(proof.message_hash)
        assert len(kwargs["content"]) == 32
        assert kwargs["headers"]["Content-Type"] == "application/octet-stream"

    @patch("httpx.Client.post")
    def test_stamp_retry_logic(self, mock_post):
        """Agota los tres servidores de la ronda y lo consigue en la siguiente.

        Cada intento de `stamp` recorre la lista completa de calendars; un
        servidor caido se salta, y solo cuando fallan los tres se consume un
        reintento. La prueba fija ese reparto: 3 fallos = 1 ronda, el exito
        llega en la ronda 2 y queda registrado como `retry_count == 1`.

        English: each `stamp` attempt walks the full calendar list; a dead
        server is skipped, and only when all three fail is a retry consumed.
        """
        client = OpenTimestampsClient(max_retries=3)
        assert len(client.servers) == 3, "la prueba asume las 3 calendars de mainnet"

        mock_post.side_effect = [
            httpx.TimeoutException("calendar a"),
            httpx.TimeoutException("calendar b"),
            httpx.ConnectError("calendar c"),
            _ots_response(OTS_SAMPLE),
        ]

        with patch("time.sleep"):
            proof = client.stamp("test")

        assert proof is not None
        assert base64.b64decode(proof.ots_response) == OTS_SAMPLE
        assert mock_post.call_count == 4
        assert client.anchor_records[-1].success is True
        assert client.anchor_records[-1].retry_count == 1

    @patch("httpx.Client.post")
    def test_stamp_max_retries_exceeded(self, mock_post):
        """OTS stamp fails after max retries."""
        import httpx

        mock_post.side_effect = httpx.TimeoutException("timeout")

        client = OpenTimestampsClient(max_retries=2)
        with patch("time.sleep"):
            proof = client.stamp("test")

        assert proof is None
        assert len(client.anchor_records) == 1
        assert client.anchor_records[0].success is False

    def test_verify_proof_valid(self):
        """Acepta un .ots estructuralmente valido."""
        proof = TimestampProof(
            timestamp=time.time(),
            message_hash="a" * 64,
            ots_response=base64.b64encode(OTS_SAMPLE).decode("ascii"),
        )

        assert OpenTimestampsClient().verify_proof(proof) is True

    def test_verify_proof_rejects_non_ots_payload(self):
        """Una cadena cualquiera no es una prueba de anclaje.

        La version anterior de esta prueba afirmaba que el texto "validproof"
        era un anclaje valido. Si alguien hubiera ajustado el codigo para
        satisfacerla, `verify_proof` habria aceptado cualquier texto como
        prueba de existencia en Bitcoin, que es justo lo que el sistema
        promete poder demostrar.

        English: the previous version of this test asserted that the string
        "validproof" was a valid anchor. Had anyone bent the code to satisfy
        it, `verify_proof` would accept any text as proof of existence in
        Bitcoin -- precisely the claim the system rests on.
        """
        client = OpenTimestampsClient()
        payloads = {
            "no es base64": "validproof",
            "base64 pero no .ots": base64.b64encode(b"not-an-ots-file").decode("ascii"),
            "byte magico incorrecto": base64.b64encode(b"\x01" + b"\x00" * 32).decode("ascii"),
            "demasiado corto": base64.b64encode(b"\x00\x01\x02").decode("ascii"),
        }
        for label, payload in payloads.items():
            proof = TimestampProof(
                timestamp=time.time(),
                message_hash="a" * 64,
                ots_response=payload,
            )
            assert client.verify_proof(proof) is False, label

    def test_verify_proof_invalid_hash(self):
        """Verify proof with invalid hash."""
        proof = TimestampProof(
            timestamp=time.time(),
            message_hash="tooshort",
            ots_response="validproof",
        )

        client = OpenTimestampsClient()
        is_valid = client.verify_proof(proof)

        assert is_valid is False

    def test_verify_proof_empty_response(self):
        """Verify proof with empty response."""
        proof = TimestampProof(
            timestamp=time.time(),
            message_hash="a" * 64,
            ots_response="",
        )

        client = OpenTimestampsClient()
        is_valid = client.verify_proof(proof)

        assert is_valid is False

    @patch("httpx.Client.post")
    def test_forensic_records(self, mock_post):
        """Export anchor attempts as forensic records."""
        mock_post.return_value = _ots_response(OTS_SAMPLE)

        client = OpenTimestampsClient()
        proof = client.stamp("message1")
        assert proof is not None

        records = client.to_forensic_records()
        assert len(records) == 1
        assert records[0]["success"] is True
        assert "checkpoint_hash" in records[0]


class TestMultichainAnchor:
    """Test multi-chain anchor with fallback."""

    def test_multichain_creation(self):
        """Create multi-chain anchor."""
        anchor = MultichainAnchor()
        assert anchor.testnet is False
        assert anchor.ots_client is not None

    @patch("vigil.anchor.opentimestamps_client.OpenTimestampsClient.stamp")
    def test_anchor_checkpoint_success(self, mock_stamp):
        """Anchor checkpoint successfully."""
        proof = TimestampProof(
            timestamp=time.time(),
            message_hash="a" * 64,
            ots_response="proof",
            bitcoin_tx="tx123",
        )
        mock_stamp.return_value = proof

        checkpoint = {
            "timestamp": "2026-05-16T00:00:00Z",
            "merkle_root": "abc123" * 10 + "abcd",
        }

        anchor = MultichainAnchor()
        result = anchor.anchor_checkpoint(checkpoint)

        assert result["bitcoin_tx"] == "tx123"
        assert result["ots_proof"] == "proof"
        assert result["anchor_chain"] == "bitcoin"

    @patch("vigil.anchor.opentimestamps_client.OpenTimestampsClient.stamp")
    def test_anchor_checkpoint_no_merkle(self, mock_stamp):
        """Anchor checkpoint without merkle root."""
        checkpoint = {"timestamp": "2026-05-16T00:00:00Z"}

        anchor = MultichainAnchor()
        result = anchor.anchor_checkpoint(checkpoint)

        # Should return unchanged (non-fatal)
        assert "bitcoin_tx" not in result
        assert mock_stamp.call_count == 0

    @patch("vigil.anchor.opentimestamps_client.OpenTimestampsClient.stamp")
    def test_anchor_checkpoint_ots_fails(self, mock_stamp):
        """Anchor checkpoint when OTS fails (no fallback configured)."""
        checkpoint = {
            "timestamp": "2026-05-16T00:00:00Z",
            "merkle_root": "abc123" * 10 + "abcd",
        }

        mock_stamp.return_value = None
        anchor = MultichainAnchor()
        result = anchor.anchor_checkpoint(checkpoint)

        # Should return checkpoint unchanged (non-fatal)
        assert "bitcoin_tx" not in result
