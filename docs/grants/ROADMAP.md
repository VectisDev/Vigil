# Roadmap

Lo que sigue es el estado real del árbol, no una lista de fases ya cerradas.
La muestra de 2025 se describe solo en [`docs/evidence/HN2025.md`](../evidence/HN2025.md).

## Hecho y comprobable

- `make replay-offline` comprueba la muestra sin red: el verificador sale en 1 (63 huérfanos) y la raíz Merkle coincide. El job `replay-offline` de `.github/workflows/ci.yml` corre ese comando en cada pull request, sin instalar `requirements.txt`.
- Pasos para un tercero: [`docs/VERIFY.md`](../VERIFY.md).
- `reachable` queda desconocido si no hay un intento registrado. Los fixtures están en `tests/fixtures/fetch_logs/`.
- Benford de primer dígito está bajado de severidad en `command_center/rules.yaml`. Hay corrección de comparaciones múltiples en `src/auditor/inconsistent_acts.py`.
- CI corre la suite de pytest, CodeQL y Dependabot. El conteo de tests no se congela en los documentos de grants.

## Preparado, no publicado

- `.github/workflows/release.yml` arma tarball, SBOM CycloneDX, `SHA256SUMS` y firma keyless. **No hay tag de software publicado por este cambio.** El mantenedor corre el comando de [`docs/operations/RELEASE.md`](../operations/RELEASE.md).
- Scorecard corre en `.github/workflows/scorecard.yml` y sube el SARIF. No hay badge en el README.
- El hash de junio de 2026 en `docs/research/THRESHOLD_PREREGISTRATION.md` ya no coincide con `rules.yaml`. El hash actual está en ese documento. Las pruebas OpenTimestamps de ese directorio siguen pendientes y no cubren el archivo de hoy.

## No hecho

- Calibración con una serie que no sea la de 2025. Si no aparece, el entregable del pedido de 75,000 USD es un resultado negativo escrito.
- Separación con compuerta de promoción entre reglas estables y experimentales. `rules.enable_research_rules` puede existir; no hay una compuerta que impida promover un umbral calibrado solo con `tests/fixtures/hnd_2025/`.
- Cobertura de todo el repositorio. Hay un piso solo sobre custodia y estadística, en el job `coverage-core`.
- Una imagen del demo está en `Dockerfile.demo` y el job `demo-image` la ejecuta. No hay un build Nix del sistema completo.
- Un segundo mantenedor. Hoy publica una persona, VectisDev.

## Pedido de fondos

75,000 USD, 12 meses, una sola tabla: [`BUDGET_NARRATIVE.md`](BUDGET_NARRATIVE.md). Quien solicita es esa persona. No hace falta un patrocinador fiscal. Uno puede considerarse más adelante. No hay ninguno. OTF acepta notas conceptuales de forma continua; este archivo no fija una fecha de envío.

---

# Roadmap (English)

What follows is the state of the tree, not a list of closed phases.
The 2025 sample is described only in [`docs/evidence/HN2025.md`](../evidence/HN2025.md).

## Done and checkable

- `make replay-offline` checks the sample with no network: the verifier exits 1 (63 orphans) and the Merkle root matches. The `replay-offline` job in `.github/workflows/ci.yml` runs that command on every pull request, without installing `requirements.txt`.
- Steps for a stranger: [`docs/VERIFY.md`](../VERIFY.md).
- `reachable` stays unknown when no attempt is recorded. Fixtures: `tests/fixtures/fetch_logs/`.
- First-digit Benford is demoted in `command_center/rules.yaml`. Multiple-comparison correction lives in `src/auditor/inconsistent_acts.py`.
- CI runs the pytest suite, CodeQL, and Dependabot. Grant docs do not freeze a test count.

## Prepared, not published

- `.github/workflows/release.yml` builds a tarball, a CycloneDX SBOM, `SHA256SUMS`, and a keyless signature. **This change does not publish a software tag.** The maintainer runs the command in [`docs/operations/RELEASE.md`](../operations/RELEASE.md).
- Scorecard runs in `.github/workflows/scorecard.yml` and uploads the SARIF. There is no badge in the README.
- The June 2026 hash in `docs/research/THRESHOLD_PREREGISTRATION.md` no longer matches `rules.yaml`. The current hash is in that document. The OpenTimestamps proofs in that directory are still pending and do not cover today's file.

## Not done

- Calibration on a series other than 2025. If none turns up, the deliverable in the 75,000 USD ask is a written negative result.
- A promotion gate between stable and experimental rules. `rules.enable_research_rules` may exist; nothing stops a threshold fit only on `tests/fixtures/hnd_2025/` from being treated as settled.
- Coverage of the whole repository. There is a floor only on custody and statistics, in the `coverage-core` job.
- The demo image is `Dockerfile.demo`, and the `demo-image` job runs it. There is no Nix build of the whole system. A bounded parser fuzz lives in `tests/test_fuzz_parsers.py`.
- A second maintainer. One person, VectisDev, publishes the tree today.

## Funding ask

75,000 USD, 12 months, one table: [`BUDGET_NARRATIVE.md`](BUDGET_NARRATIVE.md). The applicant is that person. No fiscal sponsor is needed. One may be considered later. None is in place. OTF accepts concept notes on a rolling basis; this file does not set a submission date.
