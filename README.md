<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="web/assets/logo-dark.svg">
    <img src="web/assets/logo.svg" alt="VIGIL" width="420">
  </picture>
</p>

# VIGIL

## Start here

1. Fork the repository and turn Actions on.
2. Actions → Join a room → type the room code → Run.
3. Read the color. Green: the copies match. Yellow: not yet. Red: they disagree.

On a computer: `python3 scripts/swarm_join.py CODE`

A fetch names itself `VIGIL/0.1.0 (+https://github.com/VectisDev/Vigil)`, stays under the existing ceiling of 480 requests per hour per host, and stops when `robots.txt` forbids that name. It does not disguise itself.

The pace can be changed in your own copy. A lock keeps it at or under 480 requests per hour, a 1 second gap, and a burst of 8. The lock exists to be respectful. Going past it requires `rate_override.yml` with the responsibility statement, in a signed commit. An Action refuses an unsigned override.

VIGIL keeps a saved copy of a public results feed, so a later reader can check those bytes without an account. One person maintains it, under the pseudonym VectisDev.

## Verify it yourself

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make replay-offline
```

Python 3.11+ and `make`. No network. `verify_chain.py` must exit 1 with 63 orphans. The Merkle root must be `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`.

## What it does not claim

- The 64 Honduras 2025 files are a saved sample, not a hash chain, and not a measured portal outage. Card: [`docs/evidence/HN2025.md`](docs/evidence/HN2025.md).
- It does not name a responsible party.
- There is no second maintainer, no university, and no fiscal sponsor. A sponsor may be considered later. None is in place.
- The legal name is given only to a funder at contracting. It is not in this repository.

## Next

| | |
|---|---|
| Steps and expected output | [`docs/VERIFY.md`](docs/VERIFY.md) |
| 2025 numbers | [`docs/evidence/HN2025.md`](docs/evidence/HN2025.md) |
| Report a vulnerability | [`.github/SECURITY.md`](.github/SECURITY.md) |
| What is done and not done | [`docs/grants/ROADMAP.md`](docs/grants/ROADMAP.md) |
| The only funding ask | [`docs/grants/BUDGET_NARRATIVE.md`](docs/grants/BUDGET_NARRATIVE.md) |
| Where to start | [`docs/START.md`](docs/START.md) |
| A second observer | [`docs/operations/SWARM.md`](docs/operations/SWARM.md) |

License: [AGPL-3.0](LICENSE). Security mail: vectisdev26@proton.me.
