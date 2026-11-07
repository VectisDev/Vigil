[Español](#español) · [English](#english)

---

## Español

Una persona mantiene este repositorio, con el seudónimo VectisDev. No hay equipo de seguridad ni guardia.

### Reportar una vulnerabilidad

En privado, por uno de estos dos sitios:

1. [Security → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new)
2. vectisdev26@proton.me

No abras un issue público. No hay otra dirección. No hay clave de cifrado en el repositorio. No describas una como disponible.

La bandeja se revisa con la intención de hacerlo en 14 días. Una semana perdida alarga eso. No hay acuse en un plazo corto ni una fecha prometida para la corrección. Un fallo que permita cambiar la evidencia publicada o escribir en `main` va antes que el trabajo nuevo.

### Versiones

No hay un tag de release publicado. Las correcciones entran en `main`. Cuando exista un tag, el alcance es `main` y el tag más reciente.

### Qué hace el código

- El enlace SHA-256 existe cuando el pipeline escribe `previous_hash`. Los 64 archivos de Honduras 2025 no lo tienen: `verify_chain.py` sale en 1.
- OpenTimestamps cubre una raíz Merkle cuando el archivo `.ots` existe. No es custodia continua del conteo de 2025.
- El panel en GitHub Pages es HTML estático. `web/access.json` guarda hashes, no claves. Esa puerta no es un límite de seguridad.
- CodeQL (`.github/workflows/codeql.yml`) y Dependabot (`.github/dependabot.yml`) están en el repositorio.
- El escaneo de secretos y la protección al hacer push son ajustes de GitHub. Esta página no dice que estén activos.
- No hay una auditoría de seguridad hecha por un tercero. Scorecard corre y sube un SARIF. No es una auditoría aprobada y no hay insignia en el README.

### Permisos de los workflows

El token por defecto es `contents: read`. El job que empuja commits o publica un release declara `contents: write` en ese job. No se usa `pull_request_target`.

### Texto que manda

[`.github/SECURITY.md`](https://github.com/VectisDev/Vigil/blob/main/.github/SECURITY.md). Si otra página no coincide, manda esa.

---

## English

One person maintains this repository, under the pseudonym VectisDev. There is no security team and no on-call.

### Reporting a vulnerability

In private, through one of these two places:

1. [Security → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new)
2. vectisdev26@proton.me

Do not open a public issue. There is no other address. No encryption key is in the repository. Do not describe one as available.

The inbox is checked with the intention of doing so within 14 days. A missed week makes that longer. There is no short acknowledgement clock and no promised fix date. An issue that lets someone change published evidence or write to `main` comes before new work.

### Versions

No release tag is published. Fixes land on `main`. Once a tag exists, the scope is `main` and the latest tag.

### What the code does

- The SHA-256 link exists when the pipeline writes `previous_hash`. The 64 Honduras 2025 files do not have it: `verify_chain.py` exits 1.
- OpenTimestamps covers a Merkle root when the `.ots` file exists. It is not continuous custody of the 2025 count.
- The GitHub Pages panel is static HTML. `web/access.json` stores hashes, not keys. That gate is not a security boundary.
- CodeQL (`.github/workflows/codeql.yml`) and Dependabot (`.github/dependabot.yml`) are in the repository.
- Secret scanning and push protection are GitHub settings. This page does not say they are on.
- No third-party security audit has been done. Scorecard runs and uploads SARIF. That is not a passed audit, and the README has no badge.

### Workflow permissions

The default token is `contents: read`. The job that pushes commits or publishes a release sets `contents: write` on that job. `pull_request_target` is not used.

### The file that wins

[`.github/SECURITY.md`](https://github.com/VectisDev/Vigil/blob/main/.github/SECURITY.md). If another page disagrees, that file wins.
