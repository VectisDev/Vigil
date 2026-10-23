# VIGIL

**Verificación confiable de integridad electoral — América Latina**

**Trustless electoral integrity verification — Latin America**

[Español](#español) · [English](#english)

---

## Español

Las autoridades electorales publican resultados que la ciudadanía debe aceptar por confianza. **VIGIL elimina esa confianza obligatoria**: captura los datos que la autoridad publica, los encadena criptográficamente y permite que cualquier tercero verifique —sin conexión y sin la cooperación del proyecto— que no fueron alterados después de publicarse.

> **Neutralidad.** VIGIL no afirma fraude. Detecta anomalías estadísticas en datos electorales públicos y aporta prueba criptográfica de su integridad para que personas calificadas las evalúen. Es software libre, reproducible y políticamente neutral.

### Por dónde empezar

| Si eres… | Lee |
|---|---|
| Observador, periodista o ciudadano | [Observadores — Observers](Observadores-—-Observers) |
| Operador que quiere su propia instancia | [Instalación — Setup](Instalación-—-Setup) |
| Revisor técnico o de seguridad | [Arquitectura — Architecture](Arquitectura-—-Architecture) · [Seguridad — Security](Seguridad-—-Security) |
| Estadístico o académico | [Metodología — Methodology](Metodología-—-Methodology) |
| Quien quiere ver resultados reales | [Piloto Honduras 2025 — Honduras 2025 pilot](Piloto-Honduras-2025-—-Honduras-2025-pilot) |

### En una frase por pieza

- **Captura** los datos oficiales cada pocos minutos, con límite de velocidad para no cargar el sitio de la autoridad.
- **Encadena** cada captura con SHA-256 y la ancla a Bitcoin mediante OpenTimestamps.
- **Analiza** con 24 reglas estadísticas y 7 detectores forenses.
- **Publica** un panel de verificación en [vectisdev.github.io/Vigil](https://vectisdev.github.io/Vigil/).
- **Permite verificar** todo con un único script sin dependencias: `verify/verify_chain.py`.

### Principios no negociables

- **Costo cero:** cualquiera puede operarlo sin presupuesto ni autorización.
- **Resiliencia:** no hay un punto central que incautar, bloquear o sobornar.
- **Supervivencia:** el protocolo persiste aunque su autor desaparezca; la licencia AGPL-3.0 lo garantiza.

---

## English

Electoral authorities publish results that citizens must accept on trust. **VIGIL removes that required trust**: it captures the data the authority publishes, chains it cryptographically, and lets any third party verify — offline and without the project's cooperation — that it was not altered after publication.

> **Neutrality.** VIGIL does not assert fraud. It detects statistical anomalies in public electoral data and provides cryptographic proof of its integrity for qualified human evaluation. It is free, reproducible and politically neutral software.

### Where to start

| If you are… | Read |
|---|---|
| An observer, journalist or citizen | [Observadores — Observers](Observadores-—-Observers) |
| An operator who wants their own instance | [Instalación — Setup](Instalación-—-Setup) |
| A technical or security reviewer | [Arquitectura — Architecture](Arquitectura-—-Architecture) · [Seguridad — Security](Seguridad-—-Security) |
| A statistician or academic | [Metodología — Methodology](Metodología-—-Methodology) |
| Looking for real results | [Piloto Honduras 2025 — Honduras 2025 pilot](Piloto-Honduras-2025-—-Honduras-2025-pilot) |

### One line per piece

- **Captures** official data every few minutes, rate-limited so it never burdens the authority's site.
- **Chains** every capture with SHA-256 and anchors it to Bitcoin through OpenTimestamps.
- **Analyzes** it with 24 statistical rules and 7 forensic detectors.
- **Publishes** a verification panel at [vectisdev.github.io/Vigil](https://vectisdev.github.io/Vigil/).
- **Lets anyone verify** everything with a single dependency-free script: `verify/verify_chain.py`.

### Non-negotiable principles

- **Zero cost:** anyone can run it without a budget or permission.
- **Resilience:** there is no central point to seize, block or bribe.
- **Survival:** the protocol persists even if its author disappears; the AGPL-3.0 license guarantees it.
