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


def test_export_does_not_call_unprobed_endpoints_offline(tmp_path: Path):
    """El YAML de endpoints no es una medición. Sin last_validated no hay apagón."""
    (tmp_path / "data").mkdir()
    cfg = tmp_path / "config" / "prod"
    cfg.mkdir(parents=True)
    (cfg / "endpoints.yaml").write_text(
        "cne:\n  presidential_endpoints:\n    - url: https://example.invalid/a\n",
        encoding="utf-8",
    )
    export_snapshot(tmp_path)
    health = _written(tmp_path)["endpoint_health"]
    assert health["observed"] is False
    assert health["offline"] == 0
    assert health["endpoints"][0]["status"] == "unknown"


def test_fetch_log_without_an_attempt_stays_unknown():
    """Un registro de intentos vacío no es una caída del portal."""
    state = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "fetch_logs" / "no_attempt.json").read_text(encoding="utf-8")
    )
    status = _build_cne_status(state, "https://example.invalid/")
    assert status["reachable"] is None
    assert status["last_attempt"] is None


def test_fetch_log_with_failures_is_unreachable():
    """Solo un intento registrado y fallido puede marcar la fuente como inalcanzable."""
    state = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "fetch_logs" / "consecutive_failures.json").read_text(encoding="utf-8")
    )
    status = _build_cne_status(state, "https://example.invalid/")
    assert status["reachable"] is False
    assert status["last_attempt"] == "2026-11-05T18:00:00Z"
    assert status["consecutive_failures"] == 4


def test_published_snapshot_status_matches_observations():
    """El snapshot publicado no puede afirmar salud que el documento no midió."""
    doc = json.loads((REPO_ROOT / "web" / "data" / "snapshot.json").read_text(encoding="utf-8"))
    cne = doc["cne_status"]
    if cne.get("reachable") is True:
        assert cne.get("last_attempt"), "reachable=true requires a recorded fetch attempt"
    health = doc.get("endpoint_health") or {}
    for endpoint in health.get("endpoints") or []:
        if not endpoint.get("last_validated"):
            assert endpoint.get("status") in (None, "", "unknown")


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


# ── roto e inactivo dejan de parecerse ────────────────────────────────────────
#
# Un nodo sin datos puede estar roto o estar legítimamente inactivo. Hasta aquí
# las dos cosas producían NO_DATA y salida en rojo, lo que suena correcto hasta
# que se recuerda que entre elecciones NO HAY NADA que capturar: en Honduras,
# tres años. Un rojo permanente enseña a ignorar los rojos, que es exactamente
# cómo se pierde el valor de un detector.
#
# A node with no data may be broken or legitimately idle. Both used to produce
# NO_DATA and a red exit, which sounds right until you remember there is
# nothing to collect between elections -- three years, in Honduras. A permanent
# red teaches people to ignore reds, which is how a detector loses its value.


def test_armed_declares_waiting_instead_of_failing(tmp_path: Path):
    """ARMED sin datos es correcto y debe decirlo, no fallar."""
    (tmp_path / "data").mkdir()
    export_snapshot(tmp_path, declared_mode="ARMED", mode_reason="a la espera de Honduras 2029")
    doc = _written(tmp_path)
    assert doc["status"] == "ARMED"
    assert "2029" in doc["status_reason"]
    assert doc["declared_mode"] == "ARMED"


def test_armed_never_claims_the_source_is_reachable(tmp_path: Path):
    """Estar a la espera no autoriza a afirmar nada sobre la fuente."""
    (tmp_path / "data").mkdir()
    export_snapshot(tmp_path, declared_mode="ARMED")
    assert _written(tmp_path)["cne_status"]["reachable"] is None


def test_replay_with_evidence_declares_replay(tmp_path: Path):
    """REPLAY con datos es un estado legítimo, y el panel debe distinguirlo.

    English: REPLAY with data is a legitimate state, and the panel must tell it
    apart from a live feed -- otherwise a reproduction of a 2025 dataset reads
    as current monitoring, which is the same lie in the opposite direction.
    """
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "pipeline_state.json").write_text(
        json.dumps({"cne_last_attempt_at": "2025-12-10T17:00:00Z"}), encoding="utf-8"
    )
    export_snapshot(tmp_path, declared_mode="REPLAY", mode_reason="conjunto verificado HN-2025")
    doc = _written(tmp_path)
    assert doc["status"] == "REPLAY"
    assert doc["declared_mode"] == "REPLAY"


def test_replay_without_evidence_still_fails(tmp_path: Path):
    """El detector sigue disparando donde debe.

    Declarar REPLAY y no producir datos SÍ es un fallo: el replay tenía que
    producirlos. Relajar esto convertiría el modo declarado en una forma de
    silenciar el detector, que es justo lo contrario de su propósito.

    English: declaring REPLAY and producing nothing IS a failure. Relaxing this
    would turn the declared mode into a way to silence the detector, the exact
    opposite of its purpose.
    """
    (tmp_path / "data").mkdir()
    export_snapshot(tmp_path, declared_mode="REPLAY")
    doc = _written(tmp_path)
    assert doc["status"] == "NO_DATA"
    assert "no produjo datos" in doc["status_reason"]


def test_live_without_evidence_fails_as_before(tmp_path: Path):
    """LIVE sin datos es un fallo real: debía estar capturando."""
    (tmp_path / "data").mkdir()
    export_snapshot(tmp_path, declared_mode="LIVE")
    assert _written(tmp_path)["status"] == "NO_DATA"


def test_no_declared_mode_keeps_the_previous_behaviour(tmp_path: Path):
    """Sin --mode el exportador se comporta como antes.

    Es lo que quiere una ejecución local suelta; los workflows siempre pasan el
    modo resuelto. / An ad-hoc local run wants this; workflows always pass the
    resolved mode.
    """
    (tmp_path / "data").mkdir()
    export_snapshot(tmp_path)
    doc = _written(tmp_path)
    assert doc["status"] == "NO_DATA"
    assert doc["declared_mode"] is None


# ── el replay como evidencia, y solo si está verificado ───────────────────────


def _manifest(root: Path, **fields) -> None:
    out = root / "web" / "data"
    out.mkdir(parents=True, exist_ok=True)
    base = {
        "dataset": "tests/fixtures/hnd_2025",
        "files": 64,
        "merkle_root": "f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780",
        "merkle_verified": True,
        "alerts": 21,
    }
    base.update(fields)
    (out / "replay_manifest.json").write_text(json.dumps(base), encoding="utf-8")


def test_a_verified_replay_is_evidence_on_its_own(tmp_path: Path):
    """Sin `data/`, pero con una raíz recalculada y coincidente: es REPLAY.

    English: with no `data/` but a recomputed, matching Merkle root, the node is
    in REPLAY, not NO_DATA. The root is stronger evidence than a state file: it
    says the data is the data that was anchored, not merely that a job ran.
    """
    (tmp_path / "data").mkdir()
    _manifest(tmp_path)
    export_snapshot(tmp_path, declared_mode="REPLAY")
    doc = _written(tmp_path)
    assert doc["status"] == "REPLAY"
    assert doc["replay"]["merkle_verified"] is True
    assert doc["replay"]["files"] == 64


def test_an_unverified_manifest_is_not_evidence(tmp_path: Path):
    """`merkle_verified: false` no vale como replay.

    English: a manifest that does not claim a verified root buys nothing. This
    is the hole worth closing: writing the file must not be enough to turn a
    red node green.
    """
    (tmp_path / "data").mkdir()
    _manifest(tmp_path, merkle_verified=False)
    export_snapshot(tmp_path, declared_mode="REPLAY")
    doc = _written(tmp_path)
    assert doc["status"] == "NO_DATA"
    assert "verificados" in doc["status_reason"]


def test_a_missing_merkle_verified_key_is_not_evidence(tmp_path: Path):
    """La ausencia de la clave no se interpreta a favor del nodo."""
    (tmp_path / "data").mkdir()
    out = tmp_path / "web" / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "replay_manifest.json").write_text(json.dumps({"files": 64}), encoding="utf-8")
    export_snapshot(tmp_path, declared_mode="REPLAY")
    assert _written(tmp_path)["status"] == "NO_DATA"


def test_an_unreadable_manifest_is_reported_not_swallowed(tmp_path: Path):
    """Un manifiesto corrupto se declara; no se trata como ausente en silencio.

    English: a corrupt manifest is declared rather than silently treated as
    absent, so the panel never hides a broken replay behind an empty one.
    """
    (tmp_path / "data").mkdir()
    out = tmp_path / "web" / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "replay_manifest.json").write_text("{ no es json", encoding="utf-8")
    export_snapshot(tmp_path, declared_mode="REPLAY")
    doc = _written(tmp_path)
    assert doc["status"] == "NO_DATA"
    assert doc["replay"]["merkle_verified"] is False
    assert "ilegible" in doc["replay"]["error"]


def test_replay_evidence_does_not_make_a_live_node_green(tmp_path: Path):
    """Un replay verificado no sustituye a una captura en vivo.

    English: a verified replay does not stand in for live capture. A node that
    declares LIVE with nothing but a replay manifest is still NO_DATA —
    otherwise shipping the fixture would be enough to look like an active
    observer during an election.
    """
    (tmp_path / "data").mkdir()
    _manifest(tmp_path)
    export_snapshot(tmp_path, declared_mode="LIVE")
    assert _written(tmp_path)["status"] == "NO_DATA"
