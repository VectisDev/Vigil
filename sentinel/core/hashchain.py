import hashlib
from typing import Optional


def compute_hash(canonical_json: str, previous_hash: Optional[str] = None) -> str:
    """
    Calcula el hash SHA-256 de un snapshot canónico,
    encadenado al hash anterior si existe.
    """

    hasher = hashlib.sha256()

    if previous_hash:
        hasher.update(previous_hash.encode("utf-8"))

    hasher.update(canonical_json.encode("utf-8"))
    return hasher.hexdigest()
