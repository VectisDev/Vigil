#!/usr/bin/env python3
"""
CENTINEL — Key Ceremony Script
===============================

Generate a new Ed25519 keypair and split the private key into Shamir shares
for distribution among CENTINEL custodians.

Genera un nuevo par de claves Ed25519 y divide la clave privada en shares
de Shamir para distribución entre los custodios de CENTINEL.

Usage / Uso
-----------
    python centinel_key_ceremony.py \\
        --custodians "Carlos Zelaya,Devis Alvarado,Mario Roberto Zelaya,Custodian-4,Custodian-5" \\
        --threshold 3 \\
        --output-dir ./ceremony-output/ \\
        --key-name witness_2026

This will produce:
    ./ceremony-output/witness_2026.public_key     (safe to publish)
    ./ceremony-output/witness_2026.share_01.txt   (give to Carlos Zelaya)
    ./ceremony-output/witness_2026.share_02.txt   (give to Devis Alvarado)
    ./ceremony-output/witness_2026.share_03.txt   (give to Mario Roberto Zelaya)
    ./ceremony-output/witness_2026.share_04.txt   (give to Custodian-4)
    ./ceremony-output/witness_2026.share_05.txt   (give to Custodian-5)
    ./ceremony-output/witness_2026.ceremony_record.json   (public audit record)

SECURITY REQUIREMENTS / REQUISITOS DE SEGURIDAD
-----------------------------------------------
1. RUN OFFLINE. Disconnect the network before executing this script.
   EJECUTAR OFFLINE. Desconectar la red antes de ejecutar este script.

2. EXECUTE ON A CLEAN BOOT. Use a live Linux USB (Tails recommended)
   or a wiped, freshly installed machine.

3. ALL CUSTODIANS MUST BE PHYSICALLY PRESENT during the ceremony.

4. WIPE THE WORKING DIRECTORY AFTER DISTRIBUTING SHARES. The private key
   material is deleted from memory at script exit, but disk artifacts
   must be securely removed: ``shred -u -n 7 ./ceremony-output/*``

5. The PUBLIC KEY file is the only artifact that should leave the room
   in digital form. Shares must be distributed on paper or via encrypted
   physical media (USBs cleaned and destroyed afterward).

License: AGPL-3.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# Dual-mode imports: package (installed) or standalone (air-gapped ceremony).
# Importaciones dual-mode: paquete (instalado) o standalone (ceremonia air-gapped).
try:
    from centinel.core.crypto.centinel_shamir import split_secret
    from centinel.core.crypto.centinel_share_format import serialize_share
except ModuleNotFoundError:
    # Air-gapped mode: run from same directory as the crypto modules.
    # Modo air-gapped: ejecutar desde el mismo directorio que los módulos.
    from centinel_shamir import split_secret  # type: ignore[no-redef]
    from centinel_share_format import serialize_share  # type: ignore[no-redef]

# External: cryptography (already a CENTINEL dependency).
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def _now_utc_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="centinel-key-ceremony",
        description=(
            "Generate Ed25519 keypair and Shamir-split the private key "
            "among CENTINEL custodians. MUST RUN OFFLINE."
        ),
    )
    parser.add_argument(
        "--custodians",
        required=True,
        help=(
            "Comma-separated list of custodian names. Number of names "
            "determines the total share count (n)."
        ),
    )
    parser.add_argument(
        "--threshold",
        type=int,
        required=True,
        help="Minimum shares required to reconstruct the key (k).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write share files and public key.",
    )
    parser.add_argument(
        "--key-name",
        default="witness",
        help="Filename prefix for output artifacts (default: 'witness').",
    )
    parser.add_argument(
        "--allow-online",
        action="store_true",
        help=(
            "BYPASS the offline-check. Only for automated testing. NEVER "
            "use in a real ceremony."
        ),
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help=(
            "Skip interactive confirmation. Only for automated testing. "
            "NEVER use in a real ceremony."
        ),
    )
    return parser.parse_args()


def _check_offline() -> bool:
    """
    Best-effort offline check: attempt a DNS resolution that should fail
    if network is disconnected.

    Verificación best-effort de offline: intenta una resolución DNS que
    debería fallar si la red está desconectada.
    """
    import socket

    try:
        socket.setdefaulttimeout(2)
        socket.gethostbyname("opentimestamps.org")
        return False  # Resolved -> we are ONLINE.
    except (socket.gaierror, socket.timeout, OSError):
        return True  # Failed -> we are OFFLINE (good).


def _print_banner() -> None:
    print(
        "\n"
        "============================================================\n"
        "   CENTINEL KEY CEREMONY — CRITICAL SECURITY OPERATION\n"
        "   CEREMONIA DE CLAVES CENTINEL — OPERACIÓN CRÍTICA\n"
        "============================================================\n"
    )


def _confirm(prompt: str) -> bool:
    return input(f"{prompt} [yes/no]: ").strip().lower() in {"yes", "y", "sí", "si"}


def run_ceremony(
    custodians: List[str],
    threshold: int,
    output_dir: Path,
    key_name: str,
    allow_online: bool = False,
    interactive: bool = True,
) -> dict:
    """
    Execute the full ceremony: generate keypair, split, serialize, write.

    Returns a dictionary summarizing the ceremony record (suitable for
    JSON serialization and public archival).
    """
    n_custodians = len(custodians)
    if not (2 <= threshold <= n_custodians <= 255):
        raise ValueError(
            f"Invalid configuration: threshold={threshold}, "
            f"custodians={n_custodians}. Require 2 <= threshold <= n <= 255."
        )
    if any(not c.strip() for c in custodians):
        raise ValueError("All custodian names must be non-empty")

    # 1. Offline check (overridable for tests only).
    if not allow_online and not _check_offline():
        raise RuntimeError(
            "Network is reachable. ABORTING. Disconnect network and retry. "
            "(To bypass for testing only, pass --allow-online.)"
        )

    # 2. Generate Ed25519 keypair.
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    assert len(private_bytes) == 32, "Ed25519 private key must be 32 bytes"
    assert len(public_bytes) == 32, "Ed25519 public key must be 32 bytes"

    secret_hash = hashlib.sha256(private_bytes).hexdigest()
    public_hex = public_bytes.hex()
    public_hash = hashlib.sha256(public_bytes).hexdigest()

    # 3. Split secret with Shamir.
    shares_bytes = split_secret(
        secret=private_bytes,
        threshold=threshold,
        total=n_custodians,
    )

    # 4. Confirm with operator before writing to disk.
    if interactive:
        print(f"  Custodians ({n_custodians}):")
        for i, name in enumerate(custodians, start=1):
            print(f"    {i}. {name}")
        print(f"  Threshold: {threshold} of {n_custodians}")
        print(f"  Public key (hex): {public_hex}")
        print(f"  Public key SHA-256: {public_hash}")
        print()
        if not _confirm(
            "Proceed and write share files to "
            f"{output_dir.resolve()}?"
        ):
            raise RuntimeError("Ceremony aborted by operator.")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 5. Write public key file (safe to publish).
    pubkey_path = output_dir / f"{key_name}.public_key"
    pubkey_path.write_text(
        "# CENTINEL Ed25519 Public Key — Safe to publish\n"
        f"# Created: {_now_utc_iso()}\n"
        f"# Key-Name: {key_name}\n"
        f"# Threshold-Scheme: {threshold}-of-{n_custodians}\n"
        f"# Secret-SHA256: {secret_hash}\n"
        f"# Public-Key-SHA256: {public_hash}\n"
        f"{public_hex}\n",
        encoding="utf-8",
    )
    # Set restrictive permissions (owner-only read/write).
    os.chmod(pubkey_path, 0o600)  # owner rw only

    # 6. Write each share to its own file.
    share_files: List[str] = []
    created_at = _now_utc_iso()
    for i, (custodian, share_bytes) in enumerate(
        zip(custodians, shares_bytes), start=1
    ):
        share_text = serialize_share(
            share_bytes=share_bytes,
            custodian=custodian,
            threshold=threshold,
            total=n_custodians,
            secret_hash=secret_hash,
            key_type="ed25519",
            created=created_at,
            notes=f"key_name={key_name}",
        )
        share_path = output_dir / f"{key_name}.share_{i:02d}.txt"
        share_path.write_text(share_text, encoding="utf-8")
        # Restrictive permissions on share files.
        # Permisos restrictivos en archivos de share.
        os.chmod(share_path, 0o600)
        share_files.append(str(share_path.name))

    # 7. Write ceremony record (audit log, safe to publish).
    record = {
        "ceremony_version": 1,
        "key_name": key_name,
        "created": created_at,
        "threshold": threshold,
        "total_shares": n_custodians,
        "custodians": custodians,
        "key_type": "ed25519",
        "public_key_hex": public_hex,
        "public_key_sha256": public_hash,
        "secret_sha256": secret_hash,
        "share_files": share_files,
        "tooling": {
            "tool": "centinel_key_ceremony",
            "version": "1.0",
            "shamir_field": "GF(2^8) / 0x11b",
        },
        "operator_notes": (
            "This record is safe to publish. It does NOT reveal the secret. "
            "Anyone holding `threshold` shares can reconstruct the private "
            "key and verify it matches public_key_hex and secret_sha256. "
            "Anyone holding fewer than `threshold` shares learns nothing."
        ),
    }
    record_path = output_dir / f"{key_name}.ceremony_record.json"
    record_path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.chmod(record_path, 0o640)  # owner rw, group r -- not world-readable

    if interactive:
        print()
        print("Ceremony complete. Files written to:")
        print(f"  {output_dir.resolve()}")
        print()
        print("NEXT STEPS / SIGUIENTES PASOS:")
        print(
            "  1. Distribute share files to their respective custodians "
            "via paper or encrypted physical media."
        )
        print(
            "  2. Publish the .public_key and .ceremony_record.json to "
            "the CENTINEL repository."
        )
        print(
            "  3. Securely wipe this working directory: "
            f"shred -u -n 7 {output_dir.resolve()}/*"
        )
        print(
            "  4. Anchor the ceremony record hash to OpenTimestamps for "
            "tamper-evident temporal proof."
        )
        print()

    return record


def main() -> int:
    args = parse_args()
    _print_banner()
    custodians = [c.strip() for c in args.custodians.split(",")]

    try:
        run_ceremony(
            custodians=custodians,
            threshold=args.threshold,
            output_dir=args.output_dir,
            key_name=args.key_name,
            allow_online=args.allow_online,
            interactive=not args.no_confirm,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
