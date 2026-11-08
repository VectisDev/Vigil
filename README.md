<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="web/assets/logo-dark.svg">
    <img src="web/assets/logo.svg" alt="VIGIL" width="560">
  </picture>
</p>

<h1 align="center">VIGIL</h1>

<p align="center">
  <strong>Verifiable monitoring of official public-information portals</strong><br>
  <em>Monitoreo verificable de portales oficiales de información pública</em>
</p>

<p align="center">
  <a href="https://github.com/VectisDev/Vigil/actions/workflows/ci.yml"><img src="https://github.com/VectisDev/Vigil/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="https://github.com/VectisDev/Vigil/actions/workflows/codeql.yml"><img src="https://github.com/VectisDev/Vigil/actions/workflows/codeql.yml/badge.svg?branch=main" alt="CodeQL"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-2b6cb0.svg" alt="License: AGPL-3.0"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.11%2B-2b6cb0.svg" alt="Python 3.11+"></a>
  <a href="https://zenodo.org/records/20598892"><img src="https://img.shields.io/badge/dataset-10.5281%2Fzenodo.20598892-2f855a.svg" alt="Dataset DOI"></a>
  <a href="CITATION.cff"><img src="https://img.shields.io/badge/cite-CITATION.cff-2b6cb0.svg" alt="Citation"></a>
</p>

<p align="center">
  <a href="docs/THREAT_MODEL.md">Threat model</a> ·
  <a href="docs/ORIGIN.md">Origin</a> ·
  <a href="https://github.com/VectisDev/Vigil/wiki">Wiki</a> ·
  <a href="CITATION.cff">Cite</a>
</p>

---

VIGIL watches an official portal that publishes machine-readable results. It stores what the portal published, links those captures when a capture pipeline is actually running, and records when the portal stops answering. A third party can check the stored bytes without asking the project, and without an account on the portal.

The reference case is the public JSON of Honduras' National Electoral Council (CNE) for the 2025 general election. The same capture shape applies to any authority that publishes a comparable feed.

Authorship is the pseudonym **VectisDev**. No university or party is claimed. The applicant, if a grant is filed, is that individual. The legal name is given only to the funder at contracting. No fiscal sponsor is needed. One may be considered later. None is in place.

## What a reviewer can check offline

The bundled sample is 64 official JSON files in `tests/fixtures/hnd_2025/`. Two different checks, both without network:

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil

# 1. Hash chain. These files have no previous_hash. The command must exit 1
#    and report 63 orphans. "Chain intact" here would be a false result.
python3 verify/verify_chain.py tests/fixtures/hnd_2025/

# 2. Merkle root of the same bytes. Must exit 0 and match the committed root.
#    That root is what the OpenTimestamps proof covers. It shows the files
#    existed in this form at attestation time. It is not a live chain.
python3 scripts/replay_pipeline.py \
  --dataset tests/fixtures/hnd_2025 \
  --skip-detectors \
  --out /tmp/vigil-replay
```

`make replay-offline` runs both and checks the expected outcomes. Python 3.11+ and the standard library are enough for these two commands. `PYTHONPATH` does not need to be set. The same steps, with the output to expect, are in [`docs/VERIFY.md`](docs/VERIFY.md). The 2025 numbers are in [`docs/evidence/HN2025.md`](docs/evidence/HN2025.md).

A fuller statistical pass needs the project dependencies (`pip install -r requirements.txt`) and `make reproduce-2025-audit`. That pass is not required to check custody of the bytes.

## Threat model, in short

The thing being watched is the published feed, not a ballot box. The useful failures are: the stored capture no longer matches what was stored, or the portal stops answering during a window when it had been answering. VIGIL records those events. It does not decide why they happened and it does not name a responsible party.

| Threat | What the software does |
|---|---|
| Silent change after a capture | SHA-256 link to the previous capture, when the pipeline is running and writing those links |
| Dispute about which bytes were stored | Merkle root, plus an OpenTimestamps proof when one was actually created |
| Outage of the official portal | A failed fetch is recorded as unreachable, with the attempt timestamp |
| A report that invents a healthy source | `reachable` stays unknown until a fetch is recorded. Unprobed endpoints stay `unknown`, not offline and not online |
| Load on the authority | Hard ceiling of 480 requests/hour per host |

Detail: [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).

## Honest limitations

- **The 2025 sample is retroactive.** The JSON files are public captures from 3–10 December 2025. The git history of this repository starts later. Nothing in the sample is a chain that was linked while the count was open.
- **`verify_chain.py` fails on that sample, on purpose.** 63 of the 64 files have no `previous_hash`. They are raw portal JSON. The banner for that directory is "custody not proven", and the process exits 1.
- **The Merkle root is a commitment to bytes, not continuous custody.** `tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots` covers the root `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`. It does not say when the authority published each file.
- **The 10-per-minute figure is a heuristic in code.** The 2025 sample was not a pre-registered study, and that heuristic is not a measured human capacity. The June 2026 hash in `docs/research/THRESHOLD_PREREGISTRATION.md` no longer matches `command_center/rules.yaml`. Historical series other than 2025 are not in the tree.
- **The unit of data is an aggregate.** Departmental and national JSON cannot see a single polling station. Power is low.
- **No academic institution has signed a review.** Independent review is sought. It is not in progress with a named university.
- **A panel that has not fetched the portal must say so.** `web/data/snapshot.json` in this tree is a replay of the sample. `cne_status.reachable` is null. Endpoint rows are `unknown`.

## Development

Public authorship and responsibility are VectisDev's. Parts of the code and the documentation were drafted with generative language models and then reviewed, tested, and edited in this repository. Model vendors are not authors and are not named here. The behavior a reviewer can check is the behavior of the commands above and of the test suite, not the history of a draft.

## Layout

| | |
|---|---|
| Offline chain check | [`verify/verify_chain.py`](verify/verify_chain.py) |
| Offline Merkle replay | [`scripts/replay_pipeline.py`](scripts/replay_pipeline.py) |
| Sample data | [`tests/fixtures/hnd_2025/`](tests/fixtures/hnd_2025/) |
| Threat model | [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) |
| Origin | [`docs/ORIGIN.md`](docs/ORIGIN.md) |
| Citation | [`CITATION.cff`](CITATION.cff) |

## Security

Report vulnerabilities privately: [Security → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new). See [SECURITY.md](.github/SECURITY.md).

## License

[GNU AGPL-3.0](LICENSE).

The project was formerly called CENTINEL. Some modules and documents still use that name.
