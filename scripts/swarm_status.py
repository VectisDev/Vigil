#!/usr/bin/env python3
"""Print swarm status. This is not a production join command.

Imprime el estado del enjambre. No es un comando de producción para unirse.
"""

from __future__ import annotations


def main() -> int:
    print("VIGIL swarm: not yet production")
    print("Routes exist in src/vigil/api/routes/swarm.py.")
    print("No second operator is configured.")
    print("This command does not open a port and does not join a peer.")
    print("Read docs/swarm/README.md.")
    print("Seating is a pure function for at most 12 members. It is not running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
