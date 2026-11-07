"""Bounded fuzz of the stdlib verifier and the snapshot reader.

Fuzz acotado del verificador de biblioteca estándar y del lector de snapshots.
"""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "verify" / "verify_chain.py"
SEED = 20251107
ROUNDS = 40


def _verifier():
    spec = importlib.util.spec_from_file_location("verify_chain_fuzz", VERIFIER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verifier_does_not_crash_on_random_files(tmp_path: Path) -> None:
    module = _verifier()
    rng = random.Random(SEED)
    allowed = {"intact", "orphans", "broken", "empty"}
    for index in range(ROUNDS):
        case = tmp_path / f"case-{index}"
        case.mkdir()
        kind = rng.randrange(4)
        if kind == 0:
            (case / "a.json").write_bytes(rng.randbytes(rng.randint(0, 80)))
        elif kind == 1:
            (case / "a.json").write_text("{", encoding="utf-8")
            (case / "b.json").write_text("[]", encoding="utf-8")
        elif kind == 2:
            payload = {"n": rng.randint(-5, 50), "previous_hash": "ab" * rng.randint(0, 40)}
            (case / "a.json").write_text(json.dumps(payload), encoding="utf-8")
            (case / "b.json").write_text(json.dumps({"previous_hash": None}), encoding="utf-8")
        else:
            (case / "only.json").write_text(json.dumps({"i": index}), encoding="utf-8")
        result = module.verify_chain(str(case))
        assert result["status"] in allowed
        assert result["total"] >= 0


def test_sparse_state_is_not_a_successful_fetch() -> None:
    import sys

    sys.path.insert(0, str(ROOT))
    from scripts.export_static_snapshot import _build_cne_status

    for state in ({}, {"cne_consecutive_failures": 0}, {"notes": "saved locally"}):
        status = _build_cne_status(state, "https://example.invalid/")
        assert status["reachable"] is None
        assert status["last_attempt"] is None
