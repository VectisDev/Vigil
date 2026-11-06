"""El replay reproduce un anclaje verificado, o falla.

The replay reproduces a verified anchor, or it fails.

El replay es el entregable del día uno: no hay elección que vigilar hasta 2029,
así que lo que un despliegue nuevo muestra es la reproducción local de 64
capturas reales de una elección disputada, con su raíz de Merkle confirmada en
Bitcoin por tres calendarios independientes.

Eso solo vale algo si el aserto se mantiene. Si la raíz recalculada pudiera
diferir de la comprometida sin que nada fallara, el replay sería una animación
bonita sobre datos cualesquiera.

The replay is the day-one deliverable. It is only worth something if the assert
holds: were the recomputed root allowed to differ from the committed one
without failing, the replay would be a pretty animation over arbitrary data.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
for candidate in (REPO_ROOT, REPO_ROOT / "src", SCRIPTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from replay_pipeline import (  # noqa: E402
    build_snapshot_record,
    expected_root,
    parse_timestamp_from_filename,
    _to_int,
)

DATASET = REPO_ROOT / "tests" / "fixtures" / "hnd_2025"
COMMITTED_ROOT = "f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780"


# ── el aserto central ─────────────────────────────────────────────────────────


def test_committed_root_is_read_from_the_dataset_not_hardcoded():
    """La raíz esperada sale del archivo que acompaña al conjunto.

    English: the expected root comes from the file shipped with the dataset.
    Hardcoding it in the script would let the two drift apart silently.
    """
    assert expected_root(DATASET) == COMMITTED_ROOT


def test_replay_fails_when_the_dataset_changes(tmp_path: Path):
    """Alterar un byte debe romper el replay, no pasar desapercibido.

    English: altering one byte must break the replay rather than slip through.
    This is the whole value of the assert.
    """
    fake = tmp_path / "hnd_2025"
    fake.mkdir()
    for path in sorted(DATASET.glob("*.json")):
        (fake / path.name).write_bytes(path.read_bytes())
    (fake / "MERKLE_ROOT_HN2025.txt").write_text(f"Merkle root (SHA-256): {COMMITTED_ROOT}\n", encoding="utf-8")

    # Un solo byte de diferencia en una sola captura.
    victim = sorted(fake.glob("*.json"))[0]
    victim.write_bytes(victim.read_bytes() + b" ")

    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(SCRIPTS / "replay_pipeline.py"),
            "--dataset",
            str(fake),
            "--out",
            str(tmp_path / "web"),
            "--skip-detectors",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env={"PYTHONPATH": f"{REPO_ROOT}:{REPO_ROOT / 'src'}", "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 1, "el replay deberia fallar con el conjunto alterado"
    assert "NO coincide" in result.stderr


def test_replay_succeeds_on_the_real_dataset(tmp_path: Path):
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(SCRIPTS / "replay_pipeline.py"),
            "--dataset",
            str(DATASET),
            "--out",
            str(tmp_path / "web"),
            "--skip-detectors",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env={"PYTHONPATH": f"{REPO_ROOT}:{REPO_ROOT / 'src'}", "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, result.stderr
    assert "COINCIDE" in result.stdout

    records = json.loads((tmp_path / "web" / "replay_snapshots.json").read_text(encoding="utf-8"))
    assert len(records) == 64


# ── el panel recibe lo que consume ────────────────────────────────────────────


def test_record_carries_the_fields_the_panel_reads():
    path = sorted(DATASET.glob("*.json"))[0]
    raw = json.loads(path.read_text(encoding="utf-8"))
    record = build_snapshot_record(1, path, raw, parse_timestamp_from_filename(path.name))

    for field in ("id", "captured_at", "dept_code", "raw_json", "source"):
        assert field in record
    for field in ("totalVotes", "actasEscrutadas", "actasTotal"):
        assert isinstance(record["raw_json"][field], int)
    assert record["raw_json"]["actasTotal"] > 0


def test_record_keeps_the_provenance_of_each_capture():
    """Cada registro dice de qué archivo sale y con qué hash.

    English: each record names the file it came from and its hash, so a third
    party can check any single point of the panel against the dataset.
    """
    path = sorted(DATASET.glob("*.json"))[0]
    raw = json.loads(path.read_text(encoding="utf-8"))
    record = build_snapshot_record(1, path, raw, parse_timestamp_from_filename(path.name))
    assert record["source_file"] == path.name
    assert len(record["sha256"]) == 64


def test_the_universe_of_actas_changes_mid_count():
    """Fija la observación O1 del informe: 19.152 -> 19.167.

    English: pins observation O1 from the report. A reference universe that
    changes during the count is the single hardest fact in this dataset, and
    the replay must carry it rather than smooth it away.
    """
    files = sorted(DATASET.glob("*.json"))
    totals = set()
    for index, path in enumerate(files, start=1):
        raw = json.loads(path.read_text(encoding="utf-8"))
        record = build_snapshot_record(index, path, raw, parse_timestamp_from_filename(path.name))
        totals.add(record["raw_json"]["actasTotal"])
    assert {19152, 19167}.issubset(totals)


# ── parseo del formato del CNE ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [("1,027,090", 1027090), ("19,152", 19152), ("38.10", 38), ("", 0), (None, 0), ("x", 0)],
)
def test_cne_numbers_arrive_as_text_with_commas(raw, expected):
    assert _to_int(raw) == expected


def test_timestamp_comes_from_the_filename():
    stamp = parse_timestamp_from_filename("HN.PRESIDENTE.00-TODOS.000-TODOS 2025-12-03 16_25_27.json")
    assert stamp.isoformat() == "2025-12-03T16:25:27+00:00"


def test_unparseable_filename_is_an_error_not_a_guess():
    with pytest.raises(ValueError):
        parse_timestamp_from_filename("sin-fecha.json")
