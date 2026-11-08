#!/usr/bin/env python3
"""Join a room with one code. No questions, no account.

Unirse a una sala con un código. Sin preguntas y sin cuenta.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vigil.swarm.governance import valid_room_code
from vigil.swarm.lights import SENTENCE, traffic_light


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not valid_room_code(argv[0]):
        print("That code does not work.")
        return 1
    color = traffic_light([], [], "", "")
    print(color.upper())
    print(SENTENCE[color])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
