[Español](#español) · [English](#english)

---

## Español

El detalle está en [`docs/grants/ROADMAP.md`](https://github.com/VectisDev/Vigil/blob/main/docs/grants/ROADMAP.md). Esto es el estado del árbol, no una lista de fases cerradas.

### Hecho y comprobable

- `make replay-offline` comprueba la muestra sin red: el verificador sale en 1 (63 huérfanos) y la raíz Merkle coincide. El job `replay-offline` corre en cada pull request.
- `reachable` queda desconocido si no hay un intento registrado.
- Benford de primer dígito está bajado de severidad en `command_center/rules.yaml`.

### Preparado, no publicado

- `.github/workflows/release.yml` arma tarball, SBOM, `SHA256SUMS` y firma keyless. No hay tag publicado. El comando del mantenedor está en `docs/operations/RELEASE.md`.
- Scorecard corre y sube el SARIF. No hay insignia en el README.
- El hash de junio de 2026 en `docs/research/THRESHOLD_PREREGISTRATION.md` ya no coincide con `rules.yaml`.

### No hecho

- Calibración con una serie distinta de 2025.
- Una compuerta que impida tratar como cerrado un umbral ajustado solo con `tests/fixtures/hnd_2025/`.
- Cobertura de todo el repositorio. Hay un piso sobre custodia y el exportador estático.
- Un segundo mantenedor. Hoy publica una persona, VectisDev. No hace falta un patrocinador fiscal. Uno puede considerarse más adelante. No hay ninguno.

El único pedido escrito es 75.000 USD en 12 meses, en `docs/grants/BUDGET_NARRATIVE.md`.

---

## English

The detail is in [`docs/grants/ROADMAP.md`](https://github.com/VectisDev/Vigil/blob/main/docs/grants/ROADMAP.md). This is the state of the tree, not a list of closed phases.

### Done and checkable

- `make replay-offline` checks the sample with no network: the verifier exits 1 (63 orphans) and the Merkle root matches. The `replay-offline` job runs on every pull request.
- `reachable` stays unknown when no attempt is recorded.
- First-digit Benford is demoted in `command_center/rules.yaml`.

### Prepared, not published

- `.github/workflows/release.yml` builds a tarball, an SBOM, `SHA256SUMS`, and a keyless signature. No tag is published. The maintainer's command is in `docs/operations/RELEASE.md`.
- Scorecard runs and uploads the SARIF. There is no badge in the README.
- The June 2026 hash in `docs/research/THRESHOLD_PREREGISTRATION.md` no longer matches `rules.yaml`.

### Not done

- Calibration on a series other than 2025.
- A gate that stops a threshold fit only on `tests/fixtures/hnd_2025/` from being treated as settled.
- Coverage of the whole repository. There is a floor on custody and the static exporter.
- A second maintainer. One person, VectisDev, publishes the tree today. No fiscal sponsor is needed. One may be considered later. None is in place.

The only written ask is 75,000 USD over 12 months, in `docs/grants/BUDGET_NARRATIVE.md`.
