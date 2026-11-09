# VIGIL — Observer Pack

**Para evaluadores de grants, revisores técnicos y observadores electorales internacionales.**
**For grant evaluators, technical reviewers, and international electoral observers.**

Este directorio es el punto de entrada único para comprender y evaluar VIGIL.
This directory is the single entry point to understand and evaluate VIGIL.

---

## ¿Qué es VIGIL? / What is VIGIL?

VIGIL es una herramienta de auditoría electoral de código abierto (AGPL-3.0) diseñada
específicamente para Honduras. Descarga los datos oficiales del CNE cada pocos minutos durante
el escrutinio, los encadena criptográficamente con SHA-256, y aplica 24 detectores estadísticos
para señalar anomalías estadísticas y rupturas de integridad en tiempo real.

VIGIL is an open-source electoral audit tool (AGPL-3.0) designed specifically for Honduras.
It downloads official CNE data every few minutes during the vote count, chains it cryptographically
with SHA-256, and applies statistical detectors to flag anomalies and integrity breaks in real time.

---

## Los 5 Documentos Clave / The 5 Key Documents

| # | Documento / Document | Ruta / Path | Descripción |
|---|---|---|---|
| 1 | **Theory of Change** | [`docs/grants/THEORY_OF_CHANGE.md`](../docs/grants/THEORY_OF_CHANGE.md) | Por qué reduce la asimetría de información / Why it reduces information asymmetry risk |
| 2 | **Methodology** | [`docs/research/METHODOLOGY.md`](../docs/research/METHODOLOGY.md) | Descripción técnica de los 24 detectores estadísticos / Technical description of the 24 detectors |
| 3 | **Governance** | [`docs/legal/GOVERNANCE.md`](../docs/legal/GOVERNANCE.md) | Estructura de decisión, licencia AGPL y sostenibilidad / Decision structure, AGPL license, sustainability |
| 4 | **Security Audit** | [`docs/audits/SECURITY_AUDIT.md`](../docs/audits/SECURITY_AUDIT.md) | Red-team interno RT-01..RT-15, score 9.9/10, todos cerrados / Internal red-team, all 15 issues closed |
| 5 | **False Positive Analysis** | [`docs/research/FALSE_POSITIVE_ANALYSIS.md`](../docs/research/FALSE_POSITIVE_ANALYSIS.md) | Análisis de tasa de falsas alarmas por detector / False alarm rate per detector |
| 6 | **Budget Narrative** | [`docs/grants/BUDGET_NARRATIVE.md`](../docs/grants/BUDGET_NARRATIVE.md) | Presupuesto detallado para grant OTF / Detailed OTF grant budget ($95K, 12 meses) |

---

## Demo Pública / Public Demo

**Panel en vivo / Live panel:**
`https://vectisdev.github.io/vigil/panel/`

**Reporte PDF más reciente / Latest PDF report:**
`https://vectisdev.github.io/vigil/reports/latest.pdf`

---

## Indicadores Clave / Key Indicators

| Indicador / Indicator | Valor / Value |
|---|---|
| Detectores estadísticos activos / Active detectors | 24 |
| Tests automatizados / Automated tests | 88 archivos; CI ejecuta un subconjunto de humo |
| Cobertura de seguridad / Security coverage | RT-01..RT-15 cerrados / closed |
| Revisión de seguridad / Security review | Interna; sin auditoría externa independiente |
| Licencia / License | AGPL-3.0 (copyleft de red: los derivados permanecen abiertos) |
| Lenguaje / Language | Python 3.10+ |
| Dependencias externas / External dependencies | Ninguna propietaria / None proprietary |
| Tiempo de detección / Detection latency | < 5 minutos en elecciones en vivo / < 5 min live |

---

## Contexto de Honduras / Honduras Context

- **Elecciones generales 2025:** 96 archivos JSON de resultados, 18 departamentos, ~2.5M votos
- **Institución aliada / Partner institution:** ninguna declarada / none claimed
- **Marco legal / Legal framework:** Constitución de Honduras Art. 3, Ley Electoral y de las Organizaciones Políticas
- **Relevancia:** Honduras es el único país de Centroamérica con un sistema de auditoría electoral open-source operativo

---

## Para Revisores Técnicos / For Technical Reviewers

```bash
# Clonar y ejecutar en 3 comandos / Clone and run in 3 commands
git clone https://github.com/VectisDev/Vigil
cd vigil
make install && make wizard && make pipeline
```

**Stack técnico:** Python 3.10+, FastAPI, APScheduler, SHA-256, Merkle trees, OpenTimestamps (Bitcoin)

**Arquitectura:** Static-first CDN (GitHub Pages) + pipeline autónomo + federación multi-testigo

---

## Preguntas Frecuentes de Evaluadores / Evaluator FAQ

**¿Está validado con datos reales?**
El sistema procesó los 96 JSON de resultados presidenciales de Honduras 2025. Los umbrales
fueron calibrados contra este dataset. Ver `docs/FALSE_POSITIVE_ANALYSIS.md`.

**¿Es reproducible?**
Sí. Cualquier organización puede clonar el repositorio, apuntar al endpoint del CNE y
obtener resultados idénticos. No hay componentes propietarios ni cajas negras.

**¿Qué pasa si el CNE bloquea el acceso a los datos?**
El panel web continúa sirviendo el último snapshot desde GitHub Pages (CDN), con Service
Worker para modo offline. El blackout queda registrado en la cadena de hashes.

**¿Cómo se garantiza que nadie altere los datos?**
Cada snapshot está encadenado SHA-256 con el anterior y anclado en el blockchain de Bitcoin
vía OpenTimestamps. Cualquier alteración retroactiva rompe la cadena y queda evidenciada.

---

*Último actualizado / Last updated: 2026-05-18*
*Contacto / Contact: Abre un issue en GitHub*
