"""
CENTINEL — Test suite for the key ceremony components
======================================================

Comprehensive tests for:
- GF(2^8) field arithmetic
- Shamir byte-level split/combine
- Shamir multi-byte secret split/combine
- ASCII-armored share serialization/parsing
- End-to-end key ceremony

Run with:
    pytest tests/test_key_ceremony.py -v
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

# Package import with fallback for isolated test runs.
# Importación de paquete con fallback para ejecuciones aisladas.
try:
    from centinel.core.crypto.centinel_shamir import (
        GF256, ShamirError, combine_byte, combine_shares, split_byte, split_secret,
    )
    from centinel.core.crypto.centinel_share_format import (
        Share, ShareFormatError, parse_share, serialize_share,
    )
    # Scripts are in repo root scripts/, add to path for ceremony/reconstruct imports.
    import subprocess, shutil
    _SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))
except ModuleNotFoundError:
    # Fallback: running tests directly alongside the source files.
    SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
    sys.path.insert(0, str(SCRIPTS_DIR))
    from centinel_shamir import (  # type: ignore[no-redef]
        GF256, ShamirError, combine_byte, combine_shares, split_byte, split_secret,
    )
    from centinel_share_format import (  # type: ignore[no-redef]
        Share, ShareFormatError, parse_share, serialize_share,
    )


# ---------------------------------------------------------------------------
# GF(2^8) field arithmetic tests
# ---------------------------------------------------------------------------


class TestGF256:
    def test_add_is_xor(self):
        assert GF256.add(0, 0) == 0
        assert GF256.add(0xFF, 0xFF) == 0
        assert GF256.add(0xAA, 0x55) == 0xFF
        assert GF256.add(0x12, 0x34) == 0x26

    def test_sub_equals_add(self):
        # In characteristic-2 fields, subtraction == addition.
        for a in [0, 1, 0x42, 0xFF]:
            for b in [0, 1, 0x42, 0xFF]:
                assert GF256.sub(a, b) == GF256.add(a, b)

    def test_mul_zero(self):
        for a in range(256):
            assert GF256.mul(0, a) == 0
            assert GF256.mul(a, 0) == 0

    def test_mul_identity(self):
        for a in range(256):
            assert GF256.mul(1, a) == a
            assert GF256.mul(a, 1) == a

    def test_mul_commutative(self):
        for a in [0, 1, 0x42, 0x7F, 0xFF]:
            for b in [0, 1, 0x42, 0x7F, 0xFF]:
                assert GF256.mul(a, b) == GF256.mul(b, a)

    def test_mul_associative(self):
        for a in [1, 0x42, 0xFF]:
            for b in [1, 0x7F, 0x80]:
                for c in [1, 0xAA, 0x55]:
                    lhs = GF256.mul(GF256.mul(a, b), c)
                    rhs = GF256.mul(a, GF256.mul(b, c))
                    assert lhs == rhs

    def test_mul_distributive(self):
        # a*(b+c) == a*b + a*c
        for a in range(0, 256, 17):
            for b in range(0, 256, 23):
                for c in range(0, 256, 29):
                    lhs = GF256.mul(a, GF256.add(b, c))
                    rhs = GF256.add(GF256.mul(a, b), GF256.mul(a, c))
                    assert lhs == rhs

    def test_div_inverse(self):
        # For all non-zero a: a / a == 1
        for a in range(1, 256):
            assert GF256.div(a, a) == 1

    def test_div_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            GF256.div(5, 0)

    def test_mul_div_roundtrip(self):
        # (a / b) * b == a for all a, b != 0
        for a in range(1, 256, 13):
            for b in range(1, 256, 17):
                quotient = GF256.div(a, b)
                assert GF256.mul(quotient, b) == a

    def test_exhaustive_inverse_consistency(self):
        # For every non-zero a, the multiplicative inverse satisfies a * a^-1 = 1.
        # Using div(1, a) as a^-1.
        for a in range(1, 256):
            inv = GF256.div(1, a)
            assert GF256.mul(a, inv) == 1


# ---------------------------------------------------------------------------
# Single-byte Shamir tests
# ---------------------------------------------------------------------------


class TestSplitByte:
    def test_invalid_secret_byte(self):
        with pytest.raises(ShamirError):
            split_byte(-1, 2, 3)
        with pytest.raises(ShamirError):
            split_byte(256, 2, 3)

    def test_invalid_threshold(self):
        with pytest.raises(ShamirError):
            split_byte(42, 0, 3)
        with pytest.raises(ShamirError):
            split_byte(42, 4, 3)  # threshold > total

    def test_invalid_total(self):
        with pytest.raises(ShamirError):
            split_byte(42, 2, 256)

    def test_share_count(self):
        shares = split_byte(0x42, 3, 5)
        assert len(shares) == 5
        x_values = [s[0] for s in shares]
        assert x_values == [1, 2, 3, 4, 5]

    def test_threshold_2_of_3(self):
        secret = 0x42
        shares = split_byte(secret, 2, 3)
        # Any 2 of 3 should reconstruct.
        for i, j in [(0, 1), (0, 2), (1, 2)]:
            assert combine_byte([shares[i], shares[j]]) == secret

    def test_threshold_3_of_5(self):
        secret = 0xAB
        shares = split_byte(secret, 3, 5)
        # Any 3 of 5 should reconstruct.
        from itertools import combinations

        for combo in combinations(range(5), 3):
            picked = [shares[i] for i in combo]
            assert combine_byte(picked) == secret

    def test_threshold_3_of_5_with_extra(self):
        secret = 0xAB
        shares = split_byte(secret, 3, 5)
        # Using all 5 shares (more than threshold) also works.
        assert combine_byte(shares) == secret

    def test_below_threshold_does_not_reveal_secret(self):
        """
        With only k-1 shares, the reconstruction (which is mathematically
        undefined in that case but still computes a value) should be
        statistically independent of the secret.
        """
        from collections import Counter

        # For secret S, with k=3 and only 2 shares, what does combine return?
        # The mathematical guarantee: it's a pseudo-random value, NOT the secret.
        wrong_reconstructions = 0
        trials = 100
        for _ in range(trials):
            secret = 0x42
            shares = split_byte(secret, 3, 5)
            # Use only 2 shares (below threshold 3).
            attempted = combine_byte(shares[:2])
            if attempted != secret:
                wrong_reconstructions += 1
        # Probability of accidentally getting the right value with random
        # field arithmetic is roughly 1/256. With 100 trials, almost all
        # should be wrong.
        assert wrong_reconstructions >= 95


class TestCombineByte:
    def test_no_shares_raises(self):
        with pytest.raises(ShamirError):
            combine_byte([])

    def test_duplicate_x_raises(self):
        with pytest.raises(ShamirError):
            combine_byte([(1, 10), (1, 20)])

    def test_invalid_x_zero_raises(self):
        with pytest.raises(ShamirError):
            combine_byte([(0, 10), (1, 20)])


# ---------------------------------------------------------------------------
# Multi-byte secret tests
# ---------------------------------------------------------------------------


class TestSplitSecret:
    def test_empty_secret_raises(self):
        with pytest.raises(ShamirError):
            split_secret(b"", 2, 3)

    def test_non_bytes_raises(self):
        with pytest.raises(ShamirError):
            split_secret("hello", 2, 3)  # type: ignore

    def test_share_lengths(self):
        secret = b"\x00" * 32
        shares = split_secret(secret, 3, 5)
        assert len(shares) == 5
        for s in shares:
            assert len(s) == 33  # 1 byte x + 32 bytes y

    def test_share_x_coordinates(self):
        secret = bytes(range(32))
        shares = split_secret(secret, 3, 5)
        for i, share in enumerate(shares, start=1):
            assert share[0] == i

    def test_roundtrip_random_secrets(self):
        """Splitting and recombining must recover the original secret."""
        import secrets as random_bytes

        for _ in range(20):
            length = random_bytes.choice([1, 16, 32, 64, 128])
            secret = random_bytes.token_bytes(length)
            threshold = random_bytes.choice([2, 3, 4, 5])
            total = threshold + random_bytes.choice([0, 1, 2, 3])
            shares = split_secret(secret, threshold, total)
            # Use exactly `threshold` shares for combining.
            picked = shares[:threshold]
            recovered = combine_shares(picked)
            assert recovered == secret

    def test_roundtrip_ed25519_key_size(self):
        # Ed25519 private keys are 32 bytes.
        secret = bytes.fromhex(
            "deadbeefcafebabe1234567890abcdef" * 2
        )
        assert len(secret) == 32
        shares = split_secret(secret, 3, 5)
        # Any 3 of 5 shares recovers the key.
        from itertools import combinations

        for combo in combinations(range(5), 3):
            picked = [shares[i] for i in combo]
            assert combine_shares(picked) == secret

    def test_extra_shares_above_threshold_still_works(self):
        secret = b"this is a secret message of length 39!!"
        shares = split_secret(secret, 3, 5)
        # Use all 5 shares; should still recover.
        assert combine_shares(shares) == secret


class TestCombineShares:
    def test_empty_raises(self):
        with pytest.raises(ShamirError):
            combine_shares([])

    def test_inconsistent_lengths_raises(self):
        with pytest.raises(ShamirError):
            combine_shares([b"\x01\x02\x03", b"\x02\x03"])

    def test_too_short_raises(self):
        with pytest.raises(ShamirError):
            combine_shares([b"\x01"])


# ---------------------------------------------------------------------------
# Share serialization tests
# ---------------------------------------------------------------------------


class TestShareFormat:
    SAMPLE_SHARE_BYTES = bytes([1, 0x42, 0xAB, 0xCD, 0xEF])
    SAMPLE_SECRET_HASH = "a" * 64  # placeholder hex string of correct length

    def test_serialize_basic(self):
        text = serialize_share(
            share_bytes=self.SAMPLE_SHARE_BYTES,
            custodian="Test Custodian",
            threshold=2,
            total=3,
            secret_hash=self.SAMPLE_SECRET_HASH,
            created="2026-06-08T00:00:00Z",
        )
        assert "BEGIN CENTINEL SHAMIR SHARE" in text
        assert "END CENTINEL SHAMIR SHARE" in text
        assert "Custodian: Test Custodian" in text
        assert "Share-Id: 1" in text
        assert "Threshold: 2" in text
        assert "Total: 3" in text

    def test_serialize_empty_raises(self):
        with pytest.raises(ShareFormatError):
            serialize_share(
                share_bytes=b"",
                custodian="x",
                threshold=2,
                total=3,
                secret_hash=self.SAMPLE_SECRET_HASH,
            )

    def test_serialize_with_newline_in_notes_raises(self):
        with pytest.raises(ShareFormatError):
            serialize_share(
                share_bytes=self.SAMPLE_SHARE_BYTES,
                custodian="x",
                threshold=2,
                total=3,
                secret_hash=self.SAMPLE_SECRET_HASH,
                notes="line1\nline2",
            )

    def test_parse_roundtrip(self):
        original_text = serialize_share(
            share_bytes=self.SAMPLE_SHARE_BYTES,
            custodian="Carlos Zelaya",
            threshold=3,
            total=5,
            secret_hash=self.SAMPLE_SECRET_HASH,
            created="2026-06-08T12:34:56Z",
            notes="key_name=test",
        )
        parsed = parse_share(original_text)
        assert parsed.version == 1
        assert parsed.custodian == "Carlos Zelaya"
        assert parsed.share_id == 1
        assert parsed.threshold == 3
        assert parsed.total == 5
        assert parsed.share_bytes == self.SAMPLE_SHARE_BYTES
        assert parsed.notes == "key_name=test"

    def test_parse_missing_marker_raises(self):
        with pytest.raises(ShareFormatError):
            parse_share("not a share")

    def test_parse_missing_required_header_raises(self):
        text = """-----BEGIN CENTINEL SHAMIR SHARE-----
Version: 1
Custodian: x

aGVsbG8=
-----END CENTINEL SHAMIR SHARE-----
"""
        with pytest.raises(ShareFormatError):
            parse_share(text)

    def test_parse_unsupported_version_raises(self):
        bad_text = serialize_share(
            share_bytes=self.SAMPLE_SHARE_BYTES,
            custodian="x",
            threshold=2,
            total=3,
            secret_hash=self.SAMPLE_SECRET_HASH,
        ).replace("Version: 1", "Version: 99")
        with pytest.raises(ShareFormatError):
            parse_share(bad_text)

    def test_parse_corrupted_base64_raises(self):
        bad_text = serialize_share(
            share_bytes=self.SAMPLE_SHARE_BYTES,
            custodian="x",
            threshold=2,
            total=3,
            secret_hash=self.SAMPLE_SECRET_HASH,
        )
        # Replace body with invalid base64.
        bad_text = bad_text.replace(
            "AUKrze8=",  # base64 of SAMPLE_SHARE_BYTES (if matches)
            "INVALID!!!",
        )
        # If the replacement didn't match, manually corrupt:
        if "INVALID" not in bad_text:
            lines = bad_text.splitlines()
            # Find the line after the blank line.
            for i, line in enumerate(lines):
                if line == "" and i + 1 < len(lines):
                    lines[i + 1] = "@@@INVALID@@@"
                    break
            bad_text = "\n".join(lines)
        with pytest.raises(ShareFormatError):
            parse_share(bad_text)

    def test_parse_share_hash_mismatch_raises(self):
        text = serialize_share(
            share_bytes=self.SAMPLE_SHARE_BYTES,
            custodian="x",
            threshold=2,
            total=3,
            secret_hash=self.SAMPLE_SECRET_HASH,
        )
        # Corrupt the share hash.
        corrupted = text.replace(
            "Share-Hash-SHA256: ",
            "Share-Hash-SHA256: 0000000000000000000000000000000000000000000000000000000000000000\nXXX: ",
        ).replace("XXX: ", "")
        # The above only works if the line is unique. Build differently.
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("Share-Hash-SHA256: "):
                lines[i] = "Share-Hash-SHA256: " + "00" * 32
                break
        with pytest.raises(ShareFormatError):
            parse_share("\n".join(lines) + "\n")

    def test_parse_share_id_mismatch_raises(self):
        text = serialize_share(
            share_bytes=self.SAMPLE_SHARE_BYTES,
            custodian="x",
            threshold=2,
            total=3,
            secret_hash=self.SAMPLE_SECRET_HASH,
        )
        # Corrupt Share-Id header to mismatch first byte.
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("Share-Id: "):
                lines[i] = "Share-Id: 99"
                break
        with pytest.raises(ShareFormatError):
            parse_share("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# End-to-end ceremony tests
# ---------------------------------------------------------------------------


class TestKeyCeremony:
    def test_full_ceremony_roundtrip(self, tmp_path: Path):
        """Run a real ceremony in a temp dir, then reconstruct from shares."""
        from centinel_key_ceremony import run_ceremony  # noqa: E402

        custodians = [
            "Carlos Zelaya",
            "Devis Alvarado",
            "Mario Roberto Zelaya",
            "Custodian-4",
            "Custodian-5",
        ]
        record = run_ceremony(
            custodians=custodians,
            threshold=3,
            output_dir=tmp_path,
            key_name="test_witness",
            allow_online=True,  # tests run in sandbox; bypass offline check.
            interactive=False,
        )

        # Verify all expected files exist.
        assert (tmp_path / "test_witness.public_key").exists()
        assert (tmp_path / "test_witness.ceremony_record.json").exists()
        for i in range(1, 6):
            assert (tmp_path / f"test_witness.share_{i:02d}.txt").exists()

        # Verify ceremony record matches what was generated.
        loaded_record = json.loads(
            (tmp_path / "test_witness.ceremony_record.json").read_text()
        )
        assert loaded_record["threshold"] == 3
        assert loaded_record["total_shares"] == 5
        assert loaded_record["custodians"] == custodians
        assert loaded_record["public_key_hex"] == record["public_key_hex"]

        # Reconstruct using 3 of 5 shares.
        from centinel_key_reconstruct import reconstruct  # noqa: E402

        share_paths = [tmp_path / f"test_witness.share_{i:02d}.txt" for i in (1, 3, 5)]
        pubkey_path = tmp_path / "test_witness.public_key"
        from centinel_key_reconstruct import _load_expected_public_key  # noqa: E402

        expected_pub = _load_expected_public_key(pubkey_path)
        private_bytes = reconstruct(
            share_paths=share_paths,
            expected_public_key=expected_pub,
        )

        # Verify reconstructed key matches.
        assert len(private_bytes) == 32
        assert hashlib.sha256(private_bytes).hexdigest() == record["secret_sha256"]

    def test_ceremony_with_insufficient_shares_fails(self, tmp_path: Path):
        from centinel_key_ceremony import run_ceremony  # noqa: E402
        from centinel_key_reconstruct import reconstruct  # noqa: E402

        run_ceremony(
            custodians=["A", "B", "C", "D", "E"],
            threshold=3,
            output_dir=tmp_path,
            key_name="insufficient_test",
            allow_online=True,
            interactive=False,
        )

        # Try to reconstruct with only 2 shares (below threshold 3).
        share_paths = [tmp_path / f"insufficient_test.share_{i:02d}.txt" for i in (1, 2)]
        with pytest.raises(ValueError, match="[Ii]nsufficient"):
            reconstruct(share_paths=share_paths)

    def test_ceremony_with_wrong_threshold_fails(self, tmp_path: Path):
        from centinel_key_ceremony import run_ceremony  # noqa: E402

        with pytest.raises(ValueError):
            run_ceremony(
                custodians=["A", "B"],
                threshold=3,  # Greater than total of 2.
                output_dir=tmp_path,
                key_name="bad",
                allow_online=True,
                interactive=False,
            )

    def test_shares_from_different_ceremonies_cannot_combine(self, tmp_path: Path):
        from centinel_key_ceremony import run_ceremony  # noqa: E402
        from centinel_key_reconstruct import reconstruct  # noqa: E402

        dir_a = tmp_path / "ceremony_a"
        dir_b = tmp_path / "ceremony_b"

        run_ceremony(
            custodians=["A", "B", "C", "D", "E"],
            threshold=3,
            output_dir=dir_a,
            key_name="key_a",
            allow_online=True,
            interactive=False,
        )
        run_ceremony(
            custodians=["A", "B", "C", "D", "E"],
            threshold=3,
            output_dir=dir_b,
            key_name="key_b",
            allow_online=True,
            interactive=False,
        )

        # Mix shares from both ceremonies — must fail safely.
        mixed_paths = [
            dir_a / "key_a.share_01.txt",
            dir_a / "key_a.share_02.txt",
            dir_b / "key_b.share_03.txt",
        ]
        with pytest.raises(ValueError, match="[Ii]nconsistent secret_hash"):
            reconstruct(share_paths=mixed_paths)


# ---------------------------------------------------------------------------
# Statistical property: shares below threshold reveal nothing about secret
# ---------------------------------------------------------------------------


class TestInformationTheoreticSecurity:
    """
    Verify the core information-theoretic security property:
    Fewer than k shares give no information about the secret.

    For a single byte secret, with k=2 and only 1 share, the share's y value
    should be uniformly distributed across all 256 possibilities regardless
    of the secret value.
    """

    def test_single_share_y_uniformly_distributed(self):
        from collections import Counter

        # For a fixed share index (x=1), with secret=0x42 and threshold=2,
        # the y value of share 1 is p(1) = secret + a_1 = 0x42 ⊕ a_1
        # where a_1 is uniform random in [0, 255]. So the distribution of
        # share-1 y values across many runs should be uniform.
        counts = Counter()
        trials = 5000
        for _ in range(trials):
            shares = split_byte(0x42, 2, 3)
            counts[shares[0][1]] += 1
        # Expected count per bucket ~= 5000 / 256 ~= 19.5
        # Chi-squared test: with df=255, critical value at p=0.001 is ~331.
        expected = trials / 256
        chi_squared = sum(
            (count - expected) ** 2 / expected
            for count in counts.values()
        )
        # Plus zero contributions for unobserved values.
        missing = 256 - len(counts)
        chi_squared += missing * expected  # treat missing as observed 0
        # Loose bound: 5000 trials is finite, allow significant slack.
        # At df=255, critical p=0.001 is ~331; we're checking the
        # distribution isn't obviously skewed.
        assert chi_squared < 500, (
            f"Distribution appears non-uniform (chi^2={chi_squared:.1f}); "
            "this suggests a flaw in random sampling."
        )
