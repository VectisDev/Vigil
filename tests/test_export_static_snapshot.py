"""El exportador nunca publica salud que no midió.

The exporter never publishes health it did not measure.

Estas pruebas fijan la invariante que faltaba: un pipeline roto y un pipeline
inactivo deben ser distinguibles en el documento publicado, y la ausencia de
datos debe hacer fallar al llamador en vez de commitear un documento vacío que
aparenta estar bien.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.export_static_snapshot import (  # noqa: E402
    _build_cne_status,
    _read_json_checked,
    export_snapshot,
)


def _written(root: Path) -> dict:
    return json.loads((root / "web" / "data" / "snapshot.json").read_text(encoding="utf-8"))


# ── reachable nunca se afirma sin evidencia ───────────────────────────────────


def test_reachable_is_unknown_without_any_attempt():
    """Cero intentos no es salud: debe ser None, no True."""
    status = _build_cne_status({}, "https://example.org/")
    assert status["reachable"] is None
    assert status["last_attempt"] is None


def test_reachable_true_only_after_a_successful_attempt():
    status = _build_cne_status(
        {"cne_last_attempt_at": "2026-11-05T18:00:00Z", "cne_consecutive_failures": 0},
        "https://example.org/",
    )
    assert status["reachable"] is True


def test_reachable_false_after_failures():
    status = _build_cne_status(
        {"cne_last_attempt_at": "2026-11-05T18:00:00Z", "cne_consecutive_failures": 3},
        "https://example.org/",
    )
    assert status["reachable"] is False
    assert status["consecutive_failures"] == 3


# ── ausencia de datos se declara y hace fallar ────────────────────────────────


def test_empty_tree_declares_no_data(tmp_path: Path):
    (tmp_path / "data").mkdir()
    export_snapshot(tmp_path)
    doc = _written(tmp_path)
    assert doc["status"] == "NO_DATA"
    assert doc["status_reason"]
    assert doc["cne_status"]["reachable"] is None
    assert doc["chain"]["chain_length"] == 0


def test_no_data_never_claims_reachable_true(tmp_path: Path):
    """La contradicción que se publicó en produccion: reachable=true sin intentos."""
    (tmp_path / "data").mkdir()
    export_snapshot(tmp_path)
    doc = _written(tmp_path)
    assert not (doc["cne_status"]["reachable"] and doc["cne_status"]["last_attempt"] is None)


def test_tree_with_chain_is_monitoring(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "hashes").mkdir()
    (tmp_path / "data" / "pipeline_state.json").write_text(
        json.dumps({"cne_last_attempt_at": "2026-11-05T18:00:00Z", "cne_consecutive_failures": 0}),
        encoding="utf-8",
    )
    (tmp_path / "hashes" / "h1.json").write_text(
        json.dumps({"chained_hash": "abc", "merkle_root": "def"}), encoding="utf-8"
    )
    export_snapshot(tmp_path)
    doc = _written(tmp_path)
    assert doc["status"] == "MONITORING"
    assert doc["chain"]["chain_length"] == 1


def test_unreachable_source_is_degraded_not_no_data(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "pipeline_state.json").write_text(
        json.dumps(
            {
                "cne_last_attempt_at": "2026-11-05T18:00:00Z",
                "cne_consecutive_failures": 7,
                "cne_first_unreachable_at": "2026-11-05T12:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    export_snapshot(tmp_path)
    doc = _written(tmp_path)
    assert doc["status"] == "DEGRADED"
    assert doc["cne_status"]["reachable"] is False


# ── ausente y corrupto son hechos distintos ───────────────────────────────────


def test_missing_and_unreadable_are_distinguished(tmp_path: Path):
    missing = tmp_path / "nope.json"
    assert _read_json_checked(missing) == ({}, "missing")

    corrupt = tmp_path / "bad.json"
    corrupt.write_text("{not json", encoding="utf-8")
    assert _read_json_checked(corrupt) == ({}, "unreadable")

    good = tmp_path / "ok.json"
    good.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert _read_json_checked(good) == ({"a": 1}, "ok")


# ── el entrypoint sale distinto de cero cuando no hay nada que publicar ───────


def test_main_exits_nonzero_on_no_data(tmp_path: Path, monkeypatch, capsys):
    from scripts import export_static_snapshot as mod

    (tmp_path / "data").mkdir()
    monkeypatch.setattr(sys, "argv", ["export_static_snapshot.py", "--root", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 1
