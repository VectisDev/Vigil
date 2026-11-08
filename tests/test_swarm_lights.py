"""The public status is one word and one sentence."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from vigil.swarm.bft import Attestation
from vigil.swarm.lights import SENTENCE, traffic_light

ROOT = Path(__file__).resolve().parents[1]


def _sign(node: str, digest: str) -> Attestation:
    return Attestation(node, "src", "t", digest)


def test_empty_room_is_yellow() -> None:
    assert traffic_light([], [], "src", "t") == "yellow"


def test_nine_matching_copies_are_green() -> None:
    members = [f"k{index}" for index in range(12)]
    signed = [_sign(f"k{index}", "aa") for index in range(9)]
    assert traffic_light(signed, members, "src", "t") == "green"


def test_two_different_copies_are_red() -> None:
    members = [f"k{index}" for index in range(12)]
    signed = [_sign(f"k{index}", "aa") for index in range(6)]
    signed += [_sign(f"k{index}", "bb") for index in range(6, 10)]
    assert traffic_light(signed, members, "src", "t") == "red"


def test_eight_copies_are_still_yellow() -> None:
    members = [f"k{index}" for index in range(12)]
    signed = [_sign(f"k{index}", "aa") for index in range(8)]
    assert traffic_light(signed, members, "src", "t") == "yellow"


def test_join_command_needs_only_a_code() -> None:
    bad = subprocess.run(
        [sys.executable, "scripts/swarm_join.py", "nope"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert bad.returncode == 1
    assert bad.stdout.strip() == "That code does not work."
    good = subprocess.run(
        [sys.executable, "scripts/swarm_join.py", "AB23CD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert good.returncode == 0
    assert good.stdout.splitlines() == ["YELLOW", SENTENCE["yellow"]]
    lowered = good.stdout.lower()
    assert "quorum" not in lowered
    assert "signature" not in lowered
    assert "github" not in lowered
