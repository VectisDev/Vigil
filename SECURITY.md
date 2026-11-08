# Política de seguridad

Una persona mantiene este repositorio, con el seudónimo VectisDev.
No hay un equipo de seguridad, ni una guardia, ni una organización detrás del buzón.

## Cómo reportar

En privado, por uno de estos dos canales:

1. [Aviso privado de GitHub](https://github.com/VectisDev/Vigil/security/advisories/new)
2. Correo: vectisdev26@proton.me

No abras un issue público para un fallo de seguridad. No hay otra dirección.

Este repositorio no publica una clave de cifrado. No describas una como disponible a pedido.
Para publicar una más adelante, el resumen iría en esta sección y la clave pública en `docs/security/vectisdev.asc`.
Hasta que ese archivo exista, usa uno de los dos canales. El buzón no está cifrado con una clave que este repositorio publique.

Los avisos se leen cuando esa persona revisa el buzón y vectisdev26@proton.me.
La intención es hacerlo en un plazo de unos 14 días. Una enfermedad, un viaje o una semana perdida lo alargan.
No hay un acuse con un reloj fijo, ni un número de días prometido para el arreglo.

Un fallo confirmado que permita cambiar evidencia publicada, empujar a `main` o tomar el repositorio se atiende antes que el trabajo de funciones.
Si el arreglo no va a llegar pronto, se publica una nota breve de mitigación en el aviso.
Lo demás espera al siguiente cambio.

## Versiones soportadas

No hay una etiqueta de publicación. Los arreglos de seguridad entran en la rama por defecto, `main`.
Cuando exista una etiqueta, el alcance es `main` y la última etiqueta. Las etiquetas anteriores no están soportadas.

La versión en `pyproject.toml` es `0.1.0`. Publicar esa etiqueta es un acto aparte del mantenedor (`.github/workflows/release.yml`, descrito en `docs/operations/RELEASE.md`). Esta política no afirma que la etiqueta exista.

## Pautas

En alcance: el código de este repositorio, los workflows de GitHub Actions y el sitio estático de `web/`.

Fuera de alcance: el portal de la autoridad electoral, los secretos de un fork y la ingeniería social contra quien mantiene el proyecto.
El programa registra lo que un portal publicó. No decide por qué cambió un número.

- Una captura se enlaza con SHA-256 solo cuando el pipeline escribe `previous_hash`. Los archivos de Honduras 2025 que vienen en el repositorio no tienen ese campo. `verify/verify_chain.py` sale con 1 sobre ellos. Véase `docs/evidence/HN2025.md`.
- Una raíz de Merkle puede anclarse con OpenTimestamps cuando de verdad se creó una prueba. La prueba junto a la muestra de 2025 se compromete con esa raíz. No es custodia continua durante el conteo.
- El código tiene firma Ed25519. Las claves privadas no están en este repositorio. Ningún conjunto de testigos opera desde este árbol.
- El panel (`web/ops/`, `web/replay/`) es HTML estático en GitHub Pages. El control de acceso es una comodidad, no una frontera: la página y sus datos son públicos. `web/access.json` guarda solo hashes de clave. La sesión del navegador dura 8 horas en `sessionStorage`.
- La API local comprueba `X-Vigil-Key` (aún se acepta `X-Centinel-Key`) en tiempo constante. Cambiar el repositorio en GitHub exige un token con ese permiso.
- No subas tokens, claves privadas, contraseñas ni claves del panel en claro.
- Los secretos de GitHub Actions viven en la configuración del repositorio. Los workflows los pasan como variables de entorno. No se imprimen.
- `scripts/encrypt_secrets.py` puede cifrar un archivo local. Un cifrado en git sigue siendo un secreto en git. Este repositorio no guarda una clave de firma cifrada ni una clave de Arbitrum. Arbitrum permanece apagado salvo que quien opera defina `ARBITRUM_PRIVATE_KEY` fuera del árbol.
- El `GITHUB_TOKEN` por defecto en `.github/workflows/` es `contents: read`. Un job que empuja commits o publica una versión pone `contents: write` en ese job.
- No se usa `pull_request_target`.
- CodeQL corre desde `.github/workflows/codeql.yml`.
- Dependabot está en `.github/dependabot.yml` (semanal; pip, Poetry y GitHub Actions).
- El escaneo de secretos y la protección de empuje son ajustes de GitHub. Este archivo no dice que estén activos.
- OpenSSF Scorecard corre desde `.github/workflows/scorecard.yml` y sube SARIF. Esa corrida no es una auditoría aprobada.
- Nadie externo ha terminado una auditoría de seguridad de este repositorio. `docs/audits/SECURITY_AUDIT.md` y `docs/security/SECURITY-REVIEW.md` son notas de quien lo mantiene.

`docs/security/SECURITY-POLICY.md` y `docs/compliance/SECURITY_POLICY.md` apuntan aquí.
Si no coinciden con este archivo, manda este archivo.

---

# Security policy

One person maintains this repository, under the pseudonym VectisDev.
There is no security team, no on-call rotation, and no organization behind the inbox.

## Reporting a vulnerability

Report privately, in one of these two places:

1. [GitHub private vulnerability reporting](https://github.com/VectisDev/Vigil/security/advisories/new)
2. Email: vectisdev26@proton.me

Do not open a public issue for a security bug. There is no other contact address.

No public encryption key is in this repository. Do not describe one as available on request.
To publish one later, add the fingerprint to this section and commit the public key as `docs/security/vectisdev.asc`.
Until that file exists, use one of the two channels above. The mailbox is not encrypted to a key this repository publishes.

## Supported versions

No release tag has been published. Security fixes land on the default branch, `main`.
When a tag exists, only `main` and the latest tag are in scope. Older tags are not supported.

The version string in `pyproject.toml` is `0.1.0`. Publishing that tag is a separate maintainer action (`.github/workflows/release.yml`, documented in `docs/operations/RELEASE.md`). This policy does not claim the tag exists.

## Guidelines

Reports are read when that person next checks the advisory inbox and vectisdev26@proton.me.
The intended interval is within 14 days. Illness, travel, or a missed week can make it longer.
There is no 48-hour acknowledgement and no fixed number of days in which a fix is promised.

A confirmed issue that lets someone change published evidence, push to `main`, or take the repository is handled before feature work.
If a fix will not land soon, the maintainer posts a short mitigation note on the advisory.
Everything else waits for the next change.

In scope: the source in this repository, the GitHub Actions workflows, and the static site under `web/`.

Out of scope: the electoral authority's portal, secrets on a fork, and social engineering of the maintainer.
The software records what a portal published. It does not decide why a number changed.

- A capture is linked with SHA-256 only when the pipeline writes `previous_hash`. The bundled Honduras 2025 files do not have that field. `verify/verify_chain.py` exits 1 on them. See `docs/evidence/HN2025.md`.
- A Merkle root can be anchored with OpenTimestamps when a proof file was actually created. The proof next to the 2025 sample commits to that root. It is not continuous custody during the count.
- Ed25519 signing exists in the code. Private keys are not in this repository. No witness set is operating from this tree.
- The operator panel (`web/ops/`, `web/replay/`) is static HTML on GitHub Pages. The access check is a convenience, not a boundary: the page and its data are public. `web/access.json` stores key hashes only (SHA-256 in the published format; an older local wizard wrote PBKDF2-SHA256). Plaintext keys are not committed. The browser session lasts 8 hours in `sessionStorage`.
- The local API checks `X-Vigil-Key` (the older `X-Centinel-Key` is still accepted) in constant time. Changing the repository on GitHub requires a token with that permission.
- Do not commit tokens, private keys, passwords, or plaintext panel keys.
- GitHub Actions secrets stay in the repository settings. Workflows pass them as environment variables. They are not printed.
- `scripts/encrypt_secrets.py` can encrypt a local env file. Ciphertext in git is still a secret in git. This repository does not store an encrypted signing key or an Arbitrum key. Arbitrum stays off unless an operator sets `ARBITRUM_PRIVATE_KEY` outside the tree.
- `web/access.json` holds hashes only.
- The default `GITHUB_TOKEN` in `.github/workflows/` is `contents: read`.
  A job that pushes commits or publishes a release sets `contents: write` on that job.
  A reusable gate job sets `contents: read`.
  `pull_request_target` is not used.
  The Scorecard job may set `id-token: write` and `security-events: write`. It does not add a badge to the README.
- CodeQL runs from `.github/workflows/codeql.yml` on push, on pull request, and on a weekly schedule.
- Dependabot is configured in `.github/dependabot.yml` (weekly; pip, Poetry, and GitHub Actions).
- Secret scanning and push protection are GitHub settings. This file does not say they are on. The maintainer checks that in the repository settings.
- OpenSSF Scorecard runs from `.github/workflows/scorecard.yml` and uploads SARIF. That run is not a passed audit.
- No third-party security audit has been completed. `docs/audits/SECURITY_AUDIT.md` and `docs/security/SECURITY-REVIEW.md` are the maintainer's own notes.

`docs/security/SECURITY-POLICY.md` and `docs/compliance/SECURITY_POLICY.md` point here.
If they disagree with this file, this file wins.
