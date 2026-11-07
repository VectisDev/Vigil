#!/usr/bin/env python3
"""
VIGIL — Verificador independiente de cadena de hashes.
VIGIL — Independent hash chain verifier.

This script verifies the cryptographic integrity of VIGIL's snapshot
chain WITHOUT requiring the VIGIL engine or any external dependency.
Any third party — OAS, EU, Carter Center, journalist, citizen — can
download this single file and verify the entire chain offline.

Este script verifica la integridad criptográfica de la cadena de snapshots
de VIGIL SIN requerir el motor VIGIL ni dependencia externa alguna.
Cualquier tercero — OEA, UE, Carter Center, periodista, ciudadano — puede
descargar este único archivo y verificar toda la cadena offline.

Usage / Uso:
    python verify_chain.py snapshots/          # Verify directory of JSONs
    python verify_chain.py snapshots/ -v       # Verbose: show each hash
    python verify_chain.py snapshots/ -o report.txt  # Write report to file

Requirements / Requisitos:
    Python 3.6+ (standard library only — no pip install needed)

How it works / Cómo funciona:
    1. Reads all .json files in the directory, sorted by filename.
    2. Computes SHA-256 of each file's raw bytes.
    3. Reads the "previous_hash" field from each JSON.
    4. Verifies that previous_hash matches the actual SHA-256 of the prior file.
    5. Treats a missing previous_hash (except on the first file) as an orphan.
       Orphans are a failed verification: raw JSON is not a hash chain.
    6. Exits 0 only when every file after the first is linked. Otherwise exits 1.

    A single altered byte in any file breaks the chain from that point forward.
    This is the same property that makes Bitcoin's blockchain tamper-evident.

    The bundled Honduras 2025 fixtures are official JSON without previous_hash.
    Verifying that directory must report orphans and exit 1. Custody of those
    files, if any, is the separate Merkle root, not this chain check.

License: AGPL-3.0 (same as VIGIL)
Version: 1.1.0
"""

import hashlib
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants / Constantes
# ---------------------------------------------------------------------------
HASH_ALGORITHM = "sha256"
PREVIOUS_HASH_KEYS = ("previous_hash", "prev_hash", "parent_hash", "chain_hash")
SNAPSHOT_HASH_KEY = "snapshot_hash"

# ---------------------------------------------------------------------------
# Core verification / Verificación central
# ---------------------------------------------------------------------------


def sha256_file(filepath: str) -> str:
    """Compute SHA-256 hex digest of a file's raw bytes."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_content(content: bytes) -> str:
    """Compute SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(content).hexdigest()


def find_previous_hash(data: dict) -> str | None:
    """
    Extract the previous_hash field from a parsed JSON snapshot.
    Tries multiple key names for compatibility.
    """
    if not isinstance(data, dict):
        return None
    for key in PREVIOUS_HASH_KEYS:
        if key in data:
            return str(data[key])
    # Check nested: data.meta.previous_hash, data.chain.previous_hash
    for container_key in ("meta", "chain", "integrity", "centinel"):
        if isinstance(data.get(container_key), dict):
            for key in PREVIOUS_HASH_KEYS:
                if key in data[container_key]:
                    return str(data[container_key][key])
    return None


def verify_chain(directory: str, verbose: bool = False) -> dict:
    """
    Verify the hash chain integrity of all JSON snapshots in a directory.

    Args:
        directory: Path to directory containing .json snapshot files.
        verbose: If True, print each file's hash as it's verified.

    Returns:
        dict with keys:
            total: number of files processed
            valid: number of valid chain links (the first file counts as genesis)
            broken: list of (filename, expected_hash, actual_hash) for breaks
            first_file: first file in chain (has no previous to verify)
            orphans: files after the first where previous_hash was not found
            chain_intact: True only when there is no break and no orphan
            status: "intact" | "orphans" | "broken" | "empty"
    """
    path = Path(directory)
    json_files = sorted(path.glob("*.json"))

    if not json_files:
        return {
            "total": 0,
            "valid": 0,
            "broken": [],
            "first_file": None,
            "orphans": [],
            "chain_intact": False,
            "status": "empty",
            "error": "No .json files found",
        }

    results = {
        "total": len(json_files),
        "valid": 0,
        "broken": [],
        "first_file": json_files[0].name,
        "orphans": [],
        "chain_intact": True,
        "status": "intact",
    }

    prev_hash = None

    for i, filepath in enumerate(json_files):
        # Compute hash of the raw file bytes
        file_hash = sha256_file(str(filepath))

        if verbose:
            print(f"  [{i+1:4d}/{len(json_files)}] {filepath.name}")
            print(f"         SHA-256: {file_hash}")

        # Parse JSON to find previous_hash field
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            results["broken"].append((filepath.name, "VALID_JSON", f"PARSE_ERROR: {e}"))
            results["chain_intact"] = False
            if verbose:
                print(f"         ⛔ PARSE ERROR: {e}")
            prev_hash = file_hash
            continue

        if not isinstance(data, dict):
            results["broken"].append((filepath.name, "JSON_OBJECT", type(data).__name__))
            results["chain_intact"] = False
            if verbose:
                print(f"         ⛔ NOT AN OBJECT: {type(data).__name__}")
            prev_hash = file_hash
            continue

        recorded_prev = find_previous_hash(data)

        if i == 0:
            # First file: no previous hash to verify
            if verbose:
                if recorded_prev:
                    print(f"         Genesis: prev_hash={recorded_prev[:16]}...")
                else:
                    print(f"         Genesis: no previous_hash (expected for first)")
            results["valid"] += 1
        else:
            if recorded_prev is None:
                # No previous_hash field found. This is not a successful link.
                # A directory of raw snapshots must not be reported as intact.
                results["orphans"].append(filepath.name)
                results["chain_intact"] = False
                if verbose:
                    print(f"         ⚠️  No previous_hash field found — orphan, custody not proven")
            elif recorded_prev == prev_hash:
                # Chain link is valid
                results["valid"] += 1
                if verbose:
                    print(f"         ✅ Chain valid: prev_hash matches file {json_files[i-1].name}")
            else:
                # CHAIN BREAK DETECTED
                results["broken"].append((filepath.name, prev_hash, recorded_prev))
                results["chain_intact"] = False
                if verbose:
                    print(f"         ⛔ CHAIN BREAK DETECTED")
                    print(f"            Expected: {prev_hash}")
                    print(f"            Recorded: {recorded_prev}")

        prev_hash = file_hash

    if results["broken"]:
        results["status"] = "broken"
        results["chain_intact"] = False
    elif results["orphans"]:
        # Orphans are a failed check, distinct from a hash mismatch: the files
        # were never linked. Calling that "intact" is a false green.
        results["status"] = "orphans"
        results["chain_intact"] = False
    else:
        results["status"] = "intact"
        results["chain_intact"] = True

    return results


# ---------------------------------------------------------------------------
# Report generation / Generación de reporte
# ---------------------------------------------------------------------------


def format_report(results: dict, directory: str) -> str:
    """Generate a human-readable verification report."""
    lines = [
        "=" * 70,
        "VIGIL — Hash Chain Verification Report",
        "VIGIL — Reporte de Verificación de Cadena de Hashes",
        "=" * 70,
        "",
        f"Directory / Directorio:  {os.path.abspath(directory)}",
        f"Files examined / Archivos:  {results['total']}",
        f"Valid links / Enlaces válidos:  {results['valid']}",
        f"Broken links / Enlaces rotos:  {len(results['broken'])}",
        f"Orphans (no prev_hash) / Huérfanos:  {len(results['orphans'])}",
        f"First file / Primer archivo:  {results.get('first_file', 'N/A')}",
        f"Status / Estado:  {results.get('status', 'unknown')}",
        "",
    ]

    if results.get("error"):
        lines.append(f"ERROR: {results['error']}")
        lines.append("")

    status = results.get("status")
    if status == "intact" and results["total"] > 0 and not results["orphans"]:
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║  ✅  CHAIN INTEGRITY VERIFIED — CADENA ÍNTEGRA     ║")
        lines.append("║                                                      ║")
        lines.append("║  All snapshots are cryptographically linked.         ║")
        lines.append("║  No tampering detected.                              ║")
        lines.append("║                                                      ║")
        lines.append("║  Todos los snapshots están criptográficamente        ║")
        lines.append("║  enlazados. No se detectó manipulación.              ║")
        lines.append("╚══════════════════════════════════════════════════════╝")
    elif status == "orphans" and not results["broken"]:
        orphan_count = len(results["orphans"])
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║  ⚠️  CUSTODY NOT PROVEN — CADENA NO DEMOSTRADA    ║")
        lines.append("║                                                      ║")
        lines.append("║  Files after the first have no previous_hash.        ║")
        lines.append("║  These are raw snapshots, not a verified hash chain. ║")
        lines.append("║  This is not evidence of tampering.                  ║")
        lines.append("║                                                      ║")
        lines.append("║  Hay archivos sin previous_hash (huérfanos).         ║")
        lines.append("║  Son capturas crudas, no una cadena verificada.      ║")
        lines.append("║  Esto no es evidencia de manipulación.               ║")
        lines.append("╚══════════════════════════════════════════════════════╝")
        lines.append("")
        lines.append(
            f"  Orphans / Huérfanos: {orphan_count} of {results['total']} files "
            "(the first file is genesis and is not counted as an orphan)."
        )
    else:
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║  ⛔  CHAIN INTEGRITY FAILED — CADENA ROTA          ║")
        lines.append("╚══════════════════════════════════════════════════════╝")
        lines.append("")
        for fname, expected, recorded in results["broken"]:
            lines.append(f"  BREAK at / ROTURA en: {fname}")
            lines.append(f"    Expected prev_hash: {expected}")
            lines.append(f"    Recorded prev_hash: {recorded}")
            lines.append("")

    if results["orphans"]:
        lines.append("")
        lines.append("Orphan files (no previous_hash field):")
        for fname in results["orphans"]:
            lines.append(f"  ⚠️  {fname}")

    lines.append("")
    lines.append("-" * 70)
    lines.append("Verification tool: verify_chain.py v1.1.0")
    lines.append("Algorithm: SHA-256 (NIST FIPS 180-4)")
    lines.append("This report was generated independently of the VIGIL engine.")
    lines.append("Este reporte fue generado independientemente del motor VIGIL.")
    lines.append("-" * 70)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="VIGIL — Independent hash chain verifier / Verificador independiente de cadena de hashes",
        epilog="No dependencies required. Works with Python 3.6+ standard library only.",
    )
    parser.add_argument("directory", help="Directory containing .json snapshot files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show hash of each file")
    parser.add_argument("-o", "--output", help="Write report to file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"\nVerifying chain in: {os.path.abspath(args.directory)}\n")

    results = verify_chain(args.directory, verbose=args.verbose)

    if args.json:
        output = json.dumps(results, indent=2, ensure_ascii=False)
    else:
        output = format_report(results, args.directory)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nReport written to: {args.output}")
    else:
        print(output)

    # Exit 0 only when every link was checked. Orphans are a failure.
    sys.exit(0 if results.get("status") == "intact" else 1)


if __name__ == "__main__":
    main()
