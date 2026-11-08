# If the maintainer is offline

One person publishes this repository, under the name VectisDev. There is no second maintainer in the tree. A grant, if any, is paid to that person. No fiscal sponsor is needed. One may be considered later. None is in place. The legal name is given only to the funder at contracting.

The check that does not need that person:

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make replay-offline
```

The same command is `docker build -f Dockerfile.demo -t vigil-demo . && docker run --rm vigil-demo`. It needs no pip packages. Expected result: `verify_chain.py` exits 1 with 63 orphans, and the Merkle root matches `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`.

`.github/CODEOWNERS` names `@VectisDev` so review requests have a destination. That is not a second person.

The only funding total written as an ask is 75,000 USD over 12 months, in `docs/grants/BUDGET_NARRATIVE.md`. OTF funds individuals. NLnet pays an individual after milestones. Neither requires a fiscal sponsor for this applicant.
