"""Ops access keys: one secret, one public id, a salted hash.

The person who forks the repository generates the keys and hands them to
their team. A key is 12 characters from a 62-character alphabet, drawn with
``secrets`` (a CSPRNG). That is about 71 bits. The key is the secret. Its
fingerprint is the anonymous id written into a signed commit. The file stores
a per-key salt and a PBKDF2 hash, never the key and never a name.

The public site does not see the key and does not check it.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import secrets
import string
from pathlib import Path

import yaml

ALPHABET = string.ascii_letters + string.digits
KEY_LENGTH = 12
ENTROPY_BITS = KEY_LENGTH * math.log2(len(ALPHABET))
DEFAULT_ITERATIONS = 600_000
FINGERPRINT_HEX = 16
REGISTRY_NAME = "ops_keys.yml"


def empty_registry() -> dict:
    return {
        "version": 1,
        "kdf": "pbkdf2-sha256",
        "iterations": DEFAULT_ITERATIONS,
        "alphabet_size": len(ALPHABET),
        "key_length": KEY_LENGTH,
        "entropy_bits": round(ENTROPY_BITS, 2),
        "keys": [],
    }


def generate_key() -> str:
    """Draw one key from the operating system's CSPRNG."""
    return "".join(secrets.choice(ALPHABET) for _ in range(KEY_LENGTH))


def fingerprint(key: str) -> str:
    """Public id. This is not the key. The forker matches it by hashing a key they still hold."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:FINGERPRINT_HEX]


def hash_key(key: str, salt: bytes, iterations: int = DEFAULT_ITERATIONS) -> str:
    return hashlib.pbkdf2_hmac("sha256", key.encode("utf-8"), salt, int(iterations)).hex()


def new_record(
    key: str,
    iterations: int = DEFAULT_ITERATIONS,
    replaces: str | None = None,
) -> dict:
    salt = secrets.token_bytes(16)
    return {
        "id": fingerprint(key),
        "salt": salt.hex(),
        "hash": hash_key(key, salt, iterations),
        "iterations": int(iterations),
        "status": "active",
        "replaces": replaces,
    }


def _records(registry: dict) -> list[dict]:
    rows = registry.get("keys") or []
    return [row for row in rows if isinstance(row, dict)]


def verify_key(key: str, record: dict) -> bool:
    """True when this key matches an active record. A revoked record does not match."""
    if not isinstance(key, str) or len(key) != KEY_LENGTH:
        return False
    if any(character not in ALPHABET for character in key):
        return False
    if fingerprint(key) != str(record.get("id") or ""):
        return False
    try:
        salt = bytes.fromhex(str(record.get("salt") or ""))
    except ValueError:
        return False
    iterations = int(record.get("iterations") or DEFAULT_ITERATIONS)
    got = hash_key(key, salt, iterations)
    matches = hmac.compare_digest(got, str(record.get("hash") or ""))
    return matches and record.get("status") == "active"


def verify_presented(key: str, registry: dict) -> str | None:
    """Return the public id when the presented key matches an active record."""
    found: str | None = None
    for record in _records(registry):
        if verify_key(key, record):
            found = str(record.get("id"))
    return found


def key_is_active(registry: dict, key_id: str) -> bool:
    wanted = (key_id or "").strip().lower()
    if not wanted:
        return False
    for record in _records(registry):
        if str(record.get("id") or "").lower() == wanted and record.get("status") == "active":
            return True
    return False


def action_key_is_active(action: dict, registry: dict) -> bool:
    """An ops action counts when it names an active key id. Nothing else changes."""
    if not isinstance(action, dict):
        return False
    return key_is_active(registry, str(action.get("key_id") or ""))


def revoke(registry: dict, key_id: str) -> bool:
    wanted = (key_id or "").strip().lower()
    found = False
    for record in _records(registry):
        if str(record.get("id") or "").lower() == wanted:
            record["status"] = "revoked"
            found = True
    return found


def rotate(registry: dict, key_id: str, iterations: int | None = None) -> str | None:
    """Revoke one id and append a new key that replaces it. The new key is returned once."""
    wanted = (key_id or "").strip().lower()
    if not any(str(record.get("id") or "").lower() == wanted for record in _records(registry)):
        return None
    revoke(registry, wanted)
    rounds = int(iterations or registry.get("iterations") or DEFAULT_ITERATIONS)
    key = generate_key()
    registry.setdefault("keys", []).append(new_record(key, rounds, replaces=wanted))
    return key


def issue_keys(registry: dict, count: int, iterations: int | None = None) -> list[str]:
    """Add keys. The plaintext list is for the caller to show once. It is not stored."""
    rounds = int(iterations or registry.get("iterations") or DEFAULT_ITERATIONS)
    issued: list[str] = []
    for _ in range(count):
        key = generate_key()
        registry.setdefault("keys", []).append(new_record(key, rounds))
        issued.append(key)
    return issued


def load_registry(path: Path) -> dict:
    if not path.is_file():
        return empty_registry()
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return empty_registry()
    if not isinstance(loaded, dict):
        return empty_registry()
    loaded.setdefault("keys", [])
    return loaded


def save_registry(path: Path, registry: dict) -> None:
    """Write hashes only. A field that would hold the key is an error."""
    for record in _records(registry):
        if any(name in record for name in ("key", "secret", "seed", "plaintext")):
            raise ValueError("registry cannot store a key")
        for field in ("id", "salt", "hash"):
            value = str(record.get(field) or "")
            if not value or any(character not in "0123456789abcdef" for character in value.lower()):
                raise ValueError("registry field is not a hash")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(registry, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
