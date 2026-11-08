# Start here

You do not need an account.
Ask for a room code.
Run `python3 scripts/swarm_join.py CODE`.
Green means the copies match. Yellow means not yet. Red means they disagree.
That is the whole step.

One person publishes this repository, under the pseudonym VectisDev.

## Check the bytes

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make replay-offline
```

Expected: `verify_chain.py` exits 1 with 63 orphans, and the Merkle root matches `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`. Detail: [`VERIFY.md`](VERIFY.md).

## Then read only these

| Question | File |
|---|---|
| What is the 2025 sample? | [`evidence/HN2025.md`](evidence/HN2025.md) |
| How do I report a security bug? | [`../.github/SECURITY.md`](../.github/SECURITY.md) |
| What is actually done? | [`grants/ROADMAP.md`](grants/ROADMAP.md) |
| Is there a funding ask? | [`grants/BUDGET_NARRATIVE.md`](grants/BUDGET_NARRATIVE.md) |
| Can a second person join a swarm? | [`operations/SWARM.md`](operations/SWARM.md) |

Other files in `docs/` are design notes, old drafts, or research. If one of them disagrees with the table above, the table wins. The security policy that wins is `.github/SECURITY.md`.
