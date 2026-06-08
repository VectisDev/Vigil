"""
Módulo de anclaje criptográfico vía OpenTimestamps / Bitcoin.
Cryptographic anchoring module via OpenTimestamps / Bitcoin.

Proporciona prueba temporal inmutable de que los snapshots del CNE existían
antes de un momento dado, anclada en la blockchain de Bitcoin a costo cero.

Provides immutable temporal proof that CNE snapshots existed before a given
moment, anchored in the Bitcoin blockchain at zero cost.

Uso / Usage:
    from centinel.core.anchoring import anchor_snapshot_chain, verify_anchor
    
    # Anclar el estado actual de la cadena / Anchor current chain state
    result = anchor_snapshot_chain(snapshots_dir="tests/fixtures/hnd_2025/")
    
    # Verificar un .ots existente / Verify an existing .ots
    status = verify_anchor("tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots")

Architecture:
    1. Compute SHA-256 of every .json snapshot file.
    2. Build a binary Merkle tree of all hashes.
    3. Submit the Merkle root to the OTS public calendar (free).
    4. Store the .ots proof file alongside the data.
    5. Upgrade periodically (ots upgrade) until Bitcoin confirms.

References / Referencias:
    OpenTimestamps: https://opentimestamps.org
    Protocol spec: https://github.com/opentimestamps/opentimestamps-spec
    Theorem T3: docs/architecture/ARCHITECTURE.md
"""

from __future__ import annotations

import hashlib
import io
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("centinel.core.anchoring")

# ---------------------------------------------------------------------------
# OTS Calendar servers (tried in order, first success wins)
# Servidores de calendario OTS (orden de preferencia)
# ---------------------------------------------------------------------------
OTS_CALENDARS = [
    "https://bob.btc.calendar.opentimestamps.org",
    "https://alice.btc.calendar.opentimestamps.org",
    "https://finney.calendar.eternitywall.com",
    "https://ots.btc.catallaxy.com/calendar",
]


# ---------------------------------------------------------------------------
# Result container / Contenedor de resultado
# ---------------------------------------------------------------------------
@dataclass
class AnchorResult:
    """
    Resultado de una operación de anclaje OTS.
    Result of an OTS anchoring operation.

    Attributes:
        merkle_root: SHA-256 Merkle root of all anchored files (hex).
        n_files: Number of files included in the Merkle tree.
        ots_path: Path to the saved .ots proof file.
        calendar_used: OTS calendar server that accepted the submission.
        status: 'pending' | 'confirmed' | 'failed'
        bitcoin_tx: Bitcoin transaction hash (once confirmed).
        error: Error message if status == 'failed'.
    """
    merkle_root: str
    n_files: int
    ots_path: Optional[str] = None
    calendar_used: Optional[str] = None
    status: str = "pending"
    bitcoin_tx: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Merkle tree / Árbol de Merkle
# ---------------------------------------------------------------------------
def _merkle_root(leaves: List[str]) -> str:
    """
    Construye la raíz de un árbol de Merkle SHA-256 binario.
    Build the root of a binary SHA-256 Merkle tree.

    Fórmula / Formula:
        parent = SHA256(left_bytes || right_bytes)
        Si número impar de hojas, duplicar la última.

    Args:
        leaves: Lista de hashes SHA-256 en hexadecimal.
                List of SHA-256 hashes in hexadecimal.

    Returns:
        SHA-256 Merkle root as hex string.
    """
    if not leaves:
        raise ValueError("Cannot compute Merkle root of empty list.")
    if len(leaves) == 1:
        return leaves[0]
    if len(leaves) % 2 == 1:
        leaves = leaves + [leaves[-1]]  # duplicate last leaf
    next_level = [
        hashlib.sha256(
            bytes.fromhex(leaves[i]) + bytes.fromhex(leaves[i + 1])
        ).hexdigest()
        for i in range(0, len(leaves), 2)
    ]
    return _merkle_root(next_level)


# ---------------------------------------------------------------------------
# Public API: anchor_snapshot_chain
# ---------------------------------------------------------------------------
def anchor_snapshot_chain(
    snapshots_dir: str | Path,
    *,
    glob: str = "*.json",
    output_path: Optional[str | Path] = None,
) -> AnchorResult:
    """
    Ancla todos los snapshots JSON en un directorio a Bitcoin vía OpenTimestamps.
    Anchors all JSON snapshots in a directory to Bitcoin via OpenTimestamps.

    Proceso / Process:
        1. SHA-256 de cada archivo JSON ordenado alfabéticamente.
        2. Construye árbol de Merkle sobre todos los hashes.
        3. Envía la raíz al calendario OTS público (gratuito).
        4. Guarda el archivo .ots pendiente de confirmación.

    Args:
        snapshots_dir: Directorio con los archivos .json a anclar.
                       Directory containing .json files to anchor.
        glob: Patrón de archivos / File pattern (default: '*.json').
        output_path: Ruta de salida para el .ots. Si None, se guarda en
                     snapshots_dir/MERKLE_ROOT_<timestamp>.ots.

    Returns:
        AnchorResult con estado de la operación / with operation status.

    Note:
        La confirmación en Bitcoin tarda ~1 hora (un bloque).
        Bitcoin confirmation takes ~1 hour (one block).
        Use `ots upgrade <file>.ots` later to get the Bitcoin proof.
    """
    snapshots_dir = Path(snapshots_dir)
    files = sorted(snapshots_dir.glob(glob))

    if not files:
        return AnchorResult(
            merkle_root="",
            n_files=0,
            status="failed",
            error=f"No files matching '{glob}' found in {snapshots_dir}",
        )

    # Step 1: SHA-256 each file / Paso 1: SHA-256 de cada archivo
    file_hashes = [hashlib.sha256(f.read_bytes()).hexdigest() for f in files]
    logger.info("anchoring %d files from %s", len(files), snapshots_dir)

    # Step 2: Merkle root / Paso 2: Raíz de Merkle
    root_hex = _merkle_root(file_hashes.copy())
    root_bytes = bytes.fromhex(root_hex)
    logger.info("merkle_root=%s", root_hex)

    # Step 3: Submit to OTS calendar / Paso 3: Enviar al calendario OTS
    try:
        from opentimestamps.core.timestamp import Timestamp
        from opentimestamps.calendar import RemoteCalendar
        from opentimestamps.core.serialize import StreamSerializationContext
    except ImportError:
        return AnchorResult(
            merkle_root=root_hex,
            n_files=len(files),
            status="failed",
            error="opentimestamps-client not installed. Run: pip install opentimestamps-client",
        )

    ts = Timestamp(root_bytes)
    calendar_used = None
    last_error = None

    for cal_url in OTS_CALENDARS:
        try:
            cal = RemoteCalendar(cal_url)
            cal_ts = cal.submit(root_bytes)
            ts.merge(cal_ts)
            calendar_used = cal_url
            logger.info("ots_submit_ok calendar=%s", cal_url)
            break
        except Exception as exc:
            last_error = str(exc)
            logger.warning("ots_calendar_fail url=%s error=%s", cal_url, exc)

    if calendar_used is None:
        return AnchorResult(
            merkle_root=root_hex,
            n_files=len(files),
            status="failed",
            error=f"All OTS calendars failed. Last error: {last_error}",
        )

    # Step 4: Serialize and save .ots / Paso 4: Serializar y guardar .ots
    buf = io.BytesIO()
    ctx = StreamSerializationContext(buf)
    ts.serialize(ctx)
    ots_bytes = buf.getvalue()

    if output_path is None:
        output_path = snapshots_dir / "MERKLE_ROOT_HN2025.ots"
    output_path = Path(output_path)
    output_path.write_bytes(ots_bytes)
    logger.info("ots_saved path=%s bytes=%d", output_path, len(ots_bytes))

    return AnchorResult(
        merkle_root=root_hex,
        n_files=len(files),
        ots_path=str(output_path),
        calendar_used=calendar_used,
        status="pending",
    )


# ---------------------------------------------------------------------------
# Public API: verify_anchor
# ---------------------------------------------------------------------------
def verify_anchor(ots_path: str | Path) -> dict:
    """
    Verifica un archivo .ots contra Bitcoin blockchain.
    Verify a .ots file against the Bitcoin blockchain.

    Args:
        ots_path: Ruta al archivo .ots / Path to the .ots file.

    Returns:
        Dict with keys: status, merkle_root, bitcoin_block, bitcoin_tx, error.

    Note:
        Requires internet connection to OTS calendar/Bitcoin node.
        'pending' = submitted but not yet confirmed in Bitcoin.
        'confirmed' = Bitcoin block found, timestamp is proven.
    """
    try:
        import subprocess
        result = subprocess.run(
            ["ots", "verify", str(ots_path)],
            capture_output=True, text=True, timeout=60,
        )
        output = result.stdout + result.stderr
        if "Success!" in output or "Verified" in output:
            return {"status": "confirmed", "output": output.strip()}
        elif "Pending" in output or "pending" in output:
            return {"status": "pending", "output": output.strip()}
        else:
            return {"status": "unknown", "output": output.strip()}
    except FileNotFoundError:
        return {
            "status": "error",
            "error": "ots CLI not found. Run: pip install opentimestamps-client",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
