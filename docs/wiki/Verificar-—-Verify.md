[Español](#español) · [English](#english)

---

## Español

Con Python 3.11+ y este repositorio se pueden comprobar los bytes de Honduras 2025 sin instalar el proyecto y sin red. El texto largo está en [`docs/VERIFY.md`](https://github.com/VectisDev/Vigil/blob/main/docs/VERIFY.md).

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make replay-offline
```

`make` usa `python3`. Ese objetivo no instala dependencias.

La misma comprobación en la imagen fijada:

```bash
docker build -f Dockerfile.demo -t vigil-demo .
docker run --rm vigil-demo
```

`requirements/verify.txt` no instala paquetes.

### Qué debes ver

1. `verify/verify_chain.py tests/fixtures/hnd_2025/` sale en **1**. Estado `orphans`. **63** huérfanos. El cartel es `CUSTODY NOT PROVEN — CADENA NO DEMOSTRADA`. No debe decir `CADENA ÍNTEGRA`. Salir en 1 aquí significa que los archivos no están enlazados. Un desajuste de hash es el estado `broken` y el cartel `CADENA ROTA`.
2. `scripts/replay_pipeline.py --skip-detectors` sale en **0**. La raíz es `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`.

El job `replay-offline` de `.github/workflows/ci.yml` corre esto en cada pull request, sin `requirements.txt`.

### Qué no prueba

- No prueba que el portal estuviera caído en los huecos entre nombres de archivo. No hay registro de descargas de esta muestra.
- No prueba que los archivos se encadenaran mientras el conteo estaba abierto.
- El archivo OpenTimestamps compromete la raíz Merkle, no una cadena en vivo.
- `make reproduce-2025-audit` es otro comando, con dependencias científicas. No hace falta para mirar los bytes.

---

## English

With Python 3.11+ and this repository, the Honduras 2025 bytes can be checked without installing the project and without a network. The long text is [`docs/VERIFY.md`](https://github.com/VectisDev/Vigil/blob/main/docs/VERIFY.md).

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make replay-offline
```

`make` uses `python3`. That target installs nothing.

The same check in the pinned image:

```bash
docker build -f Dockerfile.demo -t vigil-demo .
docker run --rm vigil-demo
```

`requirements/verify.txt` installs no packages.

### What you should see

1. `verify/verify_chain.py tests/fixtures/hnd_2025/` exits **1**. Status `orphans`. **63** orphans. The banner is `CUSTODY NOT PROVEN — CADENA NO DEMOSTRADA`. It must not say `CADENA ÍNTEGRA`. An exit of 1 here means the files were never linked. A hash mismatch is status `broken` and the banner `CADENA ROTA`.
2. `scripts/replay_pipeline.py --skip-detectors` exits **0**. The root is `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`.

The `replay-offline` job in `.github/workflows/ci.yml` runs this on every pull request, without `requirements.txt`.

### What this does not prove

- It does not prove the portal was down in the gaps between filenames. There is no fetch log for this sample.
- It does not prove the files were chained while the count was open.
- The OpenTimestamps file commits to the Merkle root, not to a live chain.
- `make reproduce-2025-audit` is a different command, with scientific dependencies. It is not required to check the bytes.
