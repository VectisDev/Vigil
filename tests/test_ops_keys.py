"""Ops keys are secrets and public ids. The repository stores a salted hash."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from vigil.ops_keys import (
    ALPHABET,
    ENTROPY_BITS,
    KEY_LENGTH,
    action_key_is_active,
    empty_registry,
    fingerprint,
    generate_key,
    issue_keys,
    key_is_active,
    load_registry,
    new_record,
    revoke,
    rotate,
    save_registry,
    verify_presented,
)

ROOT = Path(__file__).resolve().parents[1]


def test_a_key_is_12_characters_from_a_62_character_alphabet() -> None:
    assert len(ALPHABET) >= 62
    assert KEY_LENGTH == 12
    assert 71 < ENTROPY_BITS < 72
    source = (ROOT / "src" / "vigil" / "ops_keys.py").read_text(encoding="utf-8")
    assert "secrets.choice" in source
    assert "random.choice" not in source
    issued = {generate_key() for _ in range(20)}
    assert len(issued) > 1
    for key in issued:
        assert len(key) == 12
        assert set(key) <= set(ALPHABET)


def test_a_presented_key_matches_only_while_it_is_active(tmp_path: Path) -> None:
    registry = empty_registry()
    first, second = issue_keys(registry, 2, iterations=1)
    assert verify_presented(first, registry) == fingerprint(first)
    assert verify_presented("not-this-key", registry) is None
    same = new_record(first, iterations=1)
    assert same["hash"] != next(row["hash"] for row in registry["keys"] if row["id"] == fingerprint(first))
    revoke(registry, fingerprint(first))
    assert verify_presented(first, registry) is None
    assert key_is_active(registry, fingerprint(first)) is False
    replacement = rotate(registry, fingerprint(second), iterations=1)
    assert replacement is not None
    assert verify_presented(second, registry) is None
    assert verify_presented(replacement, registry) == fingerprint(replacement)
    assert action_key_is_active({"key_id": fingerprint(replacement)}, registry) is True
    assert action_key_is_active({"key_id": fingerprint(first)}, registry) is False
    path = tmp_path / "ops_keys.yml"
    save_registry(path, registry)
    stored = path.read_text(encoding="utf-8")
    assert first not in stored
    assert replacement not in stored
    assert key_is_active(load_registry(path), fingerprint(replacement)) is True


def test_the_registry_refuses_a_plaintext_field(tmp_path: Path) -> None:
    registry = empty_registry()
    registry["keys"] = [{"id": "ab", "salt": "cd", "hash": "ef", "key": "abcdefghijkl"}]
    with pytest.raises(ValueError):
        save_registry(tmp_path / "ops_keys.yml", registry)


def test_the_published_registry_has_no_keys_and_the_site_does_not_check_one() -> None:
    published = yaml.safe_load((ROOT / "config" / "ops_keys.yml").read_text(encoding="utf-8"))
    assert published["keys"] == []
    assert published["key_length"] == 12
    assert published["alphabet_size"] >= 62
    web = ROOT / "web"
    for path in web.rglob("*"):
        if path.suffix.lower() not in {".html", ".js"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        assert "pbkdf2" not in text
        assert "access.json" not in text
    ops = (web / "ops" / "index.html").read_text(encoding="utf-8").lower()
    assert "<script" not in ops
    wizard = (ROOT / ".github" / "scripts" / "wizard_seeds.py").read_text(encoding="utf-8")
    assert "web/access.json" not in wizard
    assert "upload-artifact" not in wizard
