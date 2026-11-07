"""The 10-per-minute heuristic is not calibrated on another election.

La heurística de 10 por minuto no está calibrada con otra elección.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "docs" / "research" / "HISTORICAL_CALIBRATION.md"


def test_earlier_honduran_series_are_absent() -> None:
    fixtures = ROOT / "tests" / "fixtures"
    for name in ("hnd_2013", "hnd_2017", "hnd_2021"):
        assert not (fixtures / name).exists(), name


def test_the_negative_result_is_written_down() -> None:
    text = NOTE.read_text(encoding="utf-8").lower()
    assert "not in this repository" in text or "are not here" in text
    assert "heuristic" in text
    assert "2013" in text and "2017" in text and "2021" in text
