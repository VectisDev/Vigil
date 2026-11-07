# VIGIL

**Registro de lo que un portal oficial publicó — una persona, seudónimo VectisDev**

**A record of what an official portal published — one person, pseudonym VectisDev**

[Español](#español) · [English](#english)

---

## Español

Las autoridades electorales publican resultados en archivos. **VIGIL guarda lo que el portal publicó** cuando hay un pipeline en marcha, y deja que un tercero mire esos bytes sin cuenta y sin pedirle permiso al proyecto. La muestra de Honduras 2025 no es una cadena: ver [Evidencia HN2025](Evidencia-HN2025-—-HN2025-evidence).

> **Quién.** Una persona, seudónimo VectisDev. No hay equipo ni fundación. El programa señala cambios en datos públicos y no nombra un responsable. Es software libre (AGPL-3.0).

### Por dónde empezar

| Si eres… | Lee |
|---|---|
| Observador, periodista o ciudadano | [Observadores — Observers](Observadores-—-Observers) |
| Operador que quiere su propia instancia | [Instalación — Setup](Instalación-—-Setup) |
| Revisor técnico o de seguridad | [Seguridad — Security](Seguridad-—-Security) · [Verificar — Verify](Verificar-—-Verify) |
| Estadístico o académico | [Metodología — Methodology](Metodología-—-Methodology) |
| Quien quiere ver la muestra de 2025 | [Evidencia HN2025 — HN2025 evidence](Evidencia-HN2025-—-HN2025-evidence) |
| Financiador o evaluador de becas | [Financiamiento y gobernanza — Funding and governance](Financiamiento-y-gobernanza-—-Funding-and-governance) · [Hoja de ruta — Roadmap](Hoja-de-ruta-—-Roadmap) |
| Quien quiere contribuir | [Contribuir — Contributing](Contribuir-—-Contributing) |

### En una frase por pieza

- **Guarda** lo que el portal publicó, con un techo de 480 peticiones por hora y por host, cuando un pipeline está corriendo.
- **Enlaza** con SHA-256 si el pipeline escribe `previous_hash`. La muestra de 2025 no lo tiene.
- **Ancla** una raíz Merkle con OpenTimestamps cuando existe un archivo `.ots`.
- **Publica** un sitio estático en [vectisdev.github.io/Vigil](https://vectisdev.github.io/Vigil/).
- **Se comprueba** con `make replay-offline`, sin red. Pasos: [Verificar — Verify](Verificar-—-Verify).

### Principios no negociables

- **Una persona.** No hay un segundo mantenedor en el árbol.
- **AGPL-3.0.** Quien lo modifica y lo ofrece en red publica el código.
- **El autor puede desaparecer.** El código queda. No hay una organización que lo herede.

---

## English

Electoral authorities publish results as files. **VIGIL stores what the portal published** when a pipeline is running, and lets a third party look at those bytes without an account and without asking the project. The Honduras 2025 sample is not a chain: see [HN2025 evidence](Evidencia-HN2025-—-HN2025-evidence).

> **Who.** One person, pseudonym VectisDev. There is no team and no foundation. The program flags changes in public data and names no responsible party. It is free software (AGPL-3.0).

### Where to start

| If you are… | Read |
|---|---|
| An observer, journalist or citizen | [Observadores — Observers](Observadores-—-Observers) |
| An operator who wants their own instance | [Instalación — Setup](Instalación-—-Setup) |
| A technical or security reviewer | [Seguridad — Security](Seguridad-—-Security) · [Verificar — Verify](Verificar-—-Verify) |
| A statistician or academic | [Metodología — Methodology](Metodología-—-Methodology) |
| Looking at the 2025 sample | [Evidencia HN2025 — HN2025 evidence](Evidencia-HN2025-—-HN2025-evidence) |
| A funder or grant reviewer | [Financiamiento y gobernanza — Funding and governance](Financiamiento-y-gobernanza-—-Funding-and-governance) · [Hoja de ruta — Roadmap](Hoja-de-ruta-—-Roadmap) |
| Looking to contribute | [Contribuir — Contributing](Contribuir-—-Contributing) |

### One line per piece

- **Stores** what the portal published, with a ceiling of 480 requests per hour per host, when a pipeline is running.
- **Links** with SHA-256 if the pipeline writes `previous_hash`. The 2025 sample does not.
- **Anchors** a Merkle root with OpenTimestamps when an `.ots` file exists.
- **Publishes** a static site at [vectisdev.github.io/Vigil](https://vectisdev.github.io/Vigil/).
- **Is checked** with `make replay-offline`, with no network. Steps: [Verificar — Verify](Verificar-—-Verify).

### Non-negotiable principles

- **One person.** There is no second maintainer in the tree.
- **AGPL-3.0.** Someone who modifies it and offers it over a network publishes the code.
- **The author can disappear.** The code remains. No organization inherits it.
