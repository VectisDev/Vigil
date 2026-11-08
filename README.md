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

A fetch names itself `Vigil/0.1.0 (+https://github.com/VectisDev/Vigil; key:<id>)`. `<id>` is the public key id (`unset` in this repository). It stays under 480 requests per hour per host and stops when `robots.txt` forbids that name. It does not disguise itself. An operator's network privacy comes from running the fetch on GitHub Actions, which uses Microsoft addresses, not from a rotating name, a proxy, or Tor.

Freedom with visible responsibility. Vigil does not forbid a faster pace. The default stays respectful: 480 requests per hour, a gap of at least 1 second, and a burst of at most 8. Going past that is the user's freedom. It counts only after a public signed commit adds `rate_override.yml`, names an active ops key id, and accepts full responsibility for the consequences, including load on the source comparable to a denial of service. The git signature is an anonymous key, not a legal name. A key registered with a GitHub account can still show that account on GitHub. There is no swarm penalty for this choice. An unsigned file does not change the pace.

The ops page is the control panel. Three clicks replace the keys: open Regenerar claves, run Regenerate Admin Seeds (`.github/workflows/regenerate-seeds.yml`), then download the artifact `vigil-keys-download-once` from that run. It expires in one day. Only the owner of that copy can run it. The workflow commits hashes in `web/access.json` and does not print the keys. The page does not show them. A key is 12 characters from a 62-character alphabet, about 71 bits.

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
