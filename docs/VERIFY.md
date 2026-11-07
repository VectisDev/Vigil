# Verify the bundled sample

A stranger with Python 3.11+ and this repository can check the Honduras 2025 bytes without installing the project and without a network.

Canonical command:

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make replay-offline
```

`make` uses `python3`. The target does not install dependencies.

## What you should see

**Step 1.** `verify/verify_chain.py tests/fixtures/hnd_2025/` exits **1**.

- Status: `orphans`
- Orphans: **63** (the first file is genesis and is not counted)
- Banner: `CUSTODY NOT PROVEN — CADENA NO DEMOSTRADA`
- You must **not** see `CADENA ÍNTEGRA` or `CHAIN INTEGRITY VERIFIED` for this directory

An exit code of 1 here means the files were never linked. It does not mean a hash mismatch was found. A real mismatch is status `broken` and the banner `CADENA ROTA`.

**Step 2.** `scripts/replay_pipeline.py --skip-detectors` exits **0**.

- Recomputed root equals committed root
- Both are `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`

The same job runs in CI on every pull request (`.github/workflows/ci.yml`, job `replay-offline`) and does not install `requirements.txt`.

## What this does not prove

- It does not prove the portal was offline in the gaps between filename timestamps. There is no fetch log for this sample. See [`docs/evidence/HN2025.md`](evidence/HN2025.md).
- It does not prove the files were chained while the count was open.
- The OpenTimestamps file next to the fixtures commits to the Merkle root only.
- Statistical output from `make reproduce-2025-audit` needs the scientific dependencies and is a separate, heavier command. It is not required to check the bytes.

## A directory that really is a chain

`verify/verify_chain.py` exits 0 only when every file after the first carries `previous_hash` equal to the SHA-256 of the previous file's raw bytes. The banner is then `CHAIN INTEGRITY VERIFIED — CADENA ÍNTEGRA`. The bundled sample is not that directory.
