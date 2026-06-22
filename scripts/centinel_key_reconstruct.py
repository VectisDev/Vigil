#!/usr/bin/env python3
"""
CENTINEL — Key Reconstruction Script
=====================================

Reconstruct an Ed25519 private key from a sufficient number of Shamir shares.

Reconstruye una clave privada Ed25519 desde un número suficiente de shares
de Shamir.

Usage / Uso
-----------
    python centinel_key_reconstruct.py \\
        --share share_01.txt --share share_03.txt --share share_05.txt \\
        --output-private-key reconstructed.key \\
        --expected-public-key witness_2026.public_key

If --expected-public-key is provided, the reconstructed private key is
verified by deriving its public key and comparing to the expected one. If
no public key is provided, the script outputs the derived public key for
manual comparison.

SECURITY REQUIREMENTS / REQUISITOS DE SEGURIDAD
-----------------------------------------------
- RUN OFFLINE.
- Reconstruction should only be performed in the presence of `threshold`
  custodians and when there is a documented operational need (e.g.,
  the primary operator is unavailable and a new operator must take over).
- After reconstruction and use, the private key file should be securely
  wiped: ``shred -u -n 7 reconstructed.key``

License: AGPL-3.0
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List

try:
    from centinel.core.crypto.centinel_shamir import combine_shares
    from centinel.core.crypto.centinel_share_format import parse_share, ShareFormatError
except ModuleNotFoundError:
    from centinel_shamir import combine_shares  # type: ignore[no-redef]
    from centinel_share_format import parse_share, ShareFormatError  # type: ignore[no-redef]

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="centinel-key-reconstruct",
        description=(
            "Reconstruct an Ed25519 private key from Shamir shares. "
            "MUST RUN OFFLINE."
        ),
    )
    parser.add_argument(
        "--share",
        action="append",
        required=True,
        type=Path,
        help=(
            "Path to a share file. Repeat for each share. Must provide at "
            "least `threshold` shares."
        ),
    )
    parser.add_argument(
        "--output-private-key",
        type=Path,
        help=(
            "Where to write the reconstructed Ed25519 private key in raw "
            "(32-byte) format. If omitted, only verification is performed "
            "and the key is not written."
        ),
    )
    parser.add_argument(
        "--expected-public-key",
        type=Path,
        help=(
            "Path to the .public_key file (created by the ceremony). If "
            "provided, the reconstruction is verified against this file."
        ),
    )
    parser.add_argument(
        "--print-public-key",
        action="store_true",
        help="Print the derived public key in hex after reconstruction.",
    )
    return parser.parse_args()


def _load_expected_public_key(path: Path) -> bytes:
    """Parse the .public_key file produced by the ceremony. Returns 32 bytes."""
    text = path.read_text(encoding="utf-8")
    hex_lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    if len(hex_lines) != 1:
        raise ValueError(
            f"{path}: expected exactly one non-comment hex line, "
            f"found {len(hex_lines)}"
        )
    return bytes.fromhex(hex_lines[0])


def reconstruct(
    share_paths: List[Path],
    expected_public_key: bytes | None = None,
) -> bytes:
    """
    Load shares, validate metadata consistency, and reconstruct the secret.

    Returns
    -------
    bytes
        The reconstructed 32-byte Ed25519 private key.
    """
    if len(share_paths) < 2:
        raise ValueError("At least 2 shares are required for reconstruction")

    parsed = []
    for path in share_paths:
        try:
            parsed.append(parse_share(path.read_text(encoding="utf-8")))
        except ShareFormatError as exc:
            raise ValueError(f"{path}: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Cannot read {path}: {exc}") from exc

    # Metadata consistency checks across all shares.
    # Verificación de consistencia de metadata entre todos los shares.
    threshold = parsed[0].threshold
    total = parsed[0].total
    secret_hash = parsed[0].secret_hash
    key_type = parsed[0].key_type
    for s in parsed[1:]:
        if s.threshold != threshold:
            raise ValueError("Inconsistent threshold across shares")
        if s.total != total:
            raise ValueError("Inconsistent total across shares")
        if s.secret_hash != secret_hash:
            raise ValueError(
                "Inconsistent secret_hash across shares — these shares are "
                "from DIFFERENT key ceremonies and cannot be combined."
            )
        if s.key_type != key_type:
            raise ValueError("Inconsistent key_type across shares")

    # Duplicate share_id check.
    ids = [s.share_id for s in parsed]
    if len(set(ids)) != len(ids):
        raise ValueError(f"Duplicate share IDs: {ids}")

    if len(parsed) < threshold:
        raise ValueError(
            f"Insufficient shares: have {len(parsed)}, need at least {threshold}"
        )

    # Combine. / Combinar.
    reconstructed = combine_shares(s.share_bytes for s in parsed)
    if len(reconstructed) != 32:
        raise ValueError(
            f"Reconstructed key has wrong length: {len(reconstructed)} (expected 32)"
        )

    # Verify against declared secret hash.
    # Verificar contra el hash declarado del secreto.
    if hashlib.sha256(reconstructed).hexdigest() != secret_hash:
        raise ValueError(
            "Reconstructed secret does NOT match the declared secret hash. "
            "Either: (a) the shares are corrupted, (b) the shares are from "
            "different ceremonies, or (c) a malicious share was submitted."
        )

    # Verify against expected public key, if provided.
    if expected_public_key is not None:
        derived = Ed25519PrivateKey.from_private_bytes(reconstructed)
        derived_pub = derived.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        if derived_pub != expected_public_key:
            raise ValueError(
                "Reconstructed key does NOT match the expected public key. "
                "Reconstruction succeeded in the math but produces a different "
                "key than the one declared by the ceremony."
            )

    return reconstructed


def main() -> int:
    args = parse_args()
    print("\nCENTINEL — KEY RECONSTRUCTION\n")

    expected_pub: bytes | None = None
    if args.expected_public_key is not None:
        try:
            expected_pub = _load_expected_public_key(args.expected_public_key)
        except (ValueError, OSError) as exc:
            print(f"ERROR loading expected public key: {exc}", file=sys.stderr)
            return 1

    try:
        private_bytes = reconstruct(
            share_paths=args.share,
            expected_public_key=expected_pub,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Reconstruction successful.")
    if expected_pub is not None:
        print("  - Verified against declared secret hash ✓")
        print("  - Verified against expected public key ✓")
    else:
        print("  - Verified against declared secret hash ✓")
        print("  - (no expected public key provided — verify manually)")

    if args.print_public_key or args.expected_public_key is None:
        derived = Ed25519PrivateKey.from_private_bytes(private_bytes)
        derived_pub_hex = derived.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()
        print(f"  Derived public key: {derived_pub_hex}")

    if args.output_private_key is not None:
        args.output_private_key.parent.mkdir(parents=True, exist_ok=True)
        args.output_private_key.write_bytes(private_bytes)
        import os
        os.chmod(args.output_private_key, 0o600)
        print(f"  Private key written to: {args.output_private_key.resolve()}")
        print(
            "  WARNING: Securely wipe this file after use: "
            f"shred -u -n 7 {args.output_private_key.resolve()}"
        )
    else:
        print("  (No output file requested — key was not written to disk)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
