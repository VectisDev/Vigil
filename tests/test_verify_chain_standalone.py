"""The standalone verifier must not call a pile of raw JSON a hash chain.

El verificador independiente no puede llamar cadena a un montón de JSON crudo.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "hnd_2025"
VERIFIER = REPO_ROOT / "verify" / "verify_chain.py"

INTACT_BANNER = "CADENA ÍNTEGRA"
INTACT_BANNER_EN = "CHAIN INTEGRITY VERIFIED"


def _load():
    spec = importlib.util.spec_from_file_location("verify_chain_standalone", VERIFIER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_linked(directory: Path, count: int = 3) -> None:
    """Write `count` JSON files whose previous_hash is the raw SHA-256 of the prior file."""
    directory.mkdir(parents=True, exist_ok=True)
    previous = None
    for index in range(count):
        body = {"i": index}
        if previous is not None:
            body["previous_hash"] = previous
        raw = json.dumps(body, sort_keys=True).encode()
        (directory / f"{index:02d}.json").write_bytes(raw)
        previous = hashlib.sha256(raw).hexdigest()


def _write_raw(directory: Path, count: int = 64) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        (directory / f"{index:02d}.json").write_text(json.dumps({"i": index}), encoding="utf-8")


def test_linked_files_are_intact(tmp_path: Path) -> None:
    _write_linked(tmp_path, 3)
    result = _load().verify_chain(str(tmp_path))
    assert result["status"] == "intact"
    assert result["chain_intact"] is True
    assert result["orphans"] == []
    assert result["valid"] == 3
    report = _load().format_report(result, str(tmp_path))
    assert INTACT_BANNER in report


def test_raw_snapshots_are_orphans_not_an_intact_chain(tmp_path: Path) -> None:
    """63 of 64 files without previous_hash must fail, and must not say the chain is intact."""
    _write_raw(tmp_path, 64)
    module = _load()
    result = module.verify_chain(str(tmp_path))
    assert result["total"] == 64
    assert result["status"] == "orphans"
    assert result["chain_intact"] is False
    assert len(result["orphans"]) == 63
    assert result["broken"] == []
    report = module.format_report(result, str(tmp_path))
    assert INTACT_BANNER not in report
    assert INTACT_BANNER_EN not in report
    assert "CADENA NO DEMOSTRADA" in report
    assert "63" in report


def test_hash_mismatch_is_a_break_not_an_orphan(tmp_path: Path) -> None:
    _write_linked(tmp_path, 3)
    broken = tmp_path / "02.json"
    payload = json.loads(broken.read_text(encoding="utf-8"))
    payload["previous_hash"] = "0" * 64
    broken.write_text(json.dumps(payload), encoding="utf-8")
    result = _load().verify_chain(str(tmp_path))
    assert result["status"] == "broken"
    assert result["chain_intact"] is False
    assert result["broken"]
    report = _load().format_report(result, str(tmp_path))
    assert "CADENA ROTA" in report
    assert INTACT_BANNER not in report


def test_cli_exits_nonzero_on_orphans(tmp_path: Path) -> None:
    _write_raw(tmp_path, 4)
    proc = subprocess.run(
        [sys.executable, str(VERIFIER), str(tmp_path), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    payload = json.loads(proc.stdout[proc.stdout.find("{") :])
    assert payload["status"] == "orphans"
    assert "CADENA ÍNTEGRA" not in proc.stdout


def test_bundled_hnd_2025_fixtures_are_not_a_hash_chain() -> None:
    """The files shipped for the pilot are official JSON. Custody is the Merkle root, not a chain."""
    module = _load()
    result = module.verify_chain(str(FIXTURES))
    assert result["total"] == 64
    assert result["status"] == "orphans"
    assert result["chain_intact"] is False
    assert len(result["orphans"]) == 63
    report = module.format_report(result, str(FIXTURES))
    assert INTACT_BANNER not in report
    assert INTACT_BANNER_EN not in report


def test_offline_replay_recomputes_the_committed_merkle_root(tmp_path: Path) -> None:
    """The positive offline check: same bytes, same Merkle root, no network."""
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "replay_pipeline.py"),
            "--dataset",
            str(FIXTURES),
            "--skip-detectors",
            "--out",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((tmp_path / "replay_manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"] == 64
    assert manifest["merkle_verified"] is True
    assert manifest["merkle_root"] == "f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780"


def test_monitor_does_not_default_to_an_intact_chain() -> None:
    html = (REPO_ROOT / "web" / "monitor" / "index.html").read_text(encoding="utf-8")
    assert 'id="hero-label">CADENA NO VERIFICADA' in html
    assert 'id="chain-badge"' in html
    # The static badge, before any snapshot is applied, must not claim integrity.
    badge = html.split('id="chain-badge"', 1)[1].split("</div>", 1)[0]
    assert "CADENA ÍNTEGRA" not in badge
