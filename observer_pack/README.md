# Centinel Engine — Observer Pack

**Para evaluadores de grants, revisores técnicos y observadores electorales internacionales.**
**For grant evaluators, technical reviewers, and international electoral observers.**

Este directorio es el punto de entrada único para comprender y evaluar Centinel Engine.
This directory is the single entry point to understand and evaluate Centinel Engine.

---

## ¿Qué es Centinel Engine? / What is Centinel Engine?

Centinel Engine es una herramienta de auditoría electoral de código abierto (AGPL-3.0) diseñada
específicamente para Honduras. Descarga los datos oficiales del CNE cada pocos minutos durante
el escrutinio, los encadena criptográficamente con SHA-256, y aplica 24 detectores estadísticos
para detectar manipulación en tiempo real.

Centinel Engine is an open-source electoral audit tool (AGPL-3.0) designed specifically for Honduras.
It downloads official CNE data every few minutes during the vote count, chains it cryptographically
with SHA-256, and applies 24 statistical detectors to detect manipulation in real time.

---

## Los 5 Documentos Clave / The 5 Key Documents

| # | Documento / Document | Ruta / Path | Descripción |
|---|---|---|---|
| 1 | **Theory of Change** | [`docs/THEORY_OF_CHANGE.md`](../docs/THEORY_OF_CHANGE.md) | Por qué este sistema reduce el riesgo de fraude / Why this system reduces fraud risk |
| 2 | **Methodology** | [`docs/METHODOLOGY.md`](../docs/METHODOLOGY.md) | Descripción técnica de los 24 detectores estadísticos / Technical description of the 24 detectors |
| 3 | **Governance** | [`docs/GOVERNANCE.md`](../docs/GOVERNANCE.md) | Estructura de decisión, licencia AGPL y sostenibilidad / Decision structure, AGPL license, sustainability |
| 4 | **Security Audit** | [`SECURITY_AUDIT.md`](../SECURITY_AUDIT.md) | Red-team interno RT-01..RT-15, score 9.9/10, todos cerrados / Internal red-team, all 15 issues closed |
| 5 | **False Positive Analysis** | [`docs/FALSE_POSITIVE_ANALYSIS.md`](../docs/FALSE_POSITIVE_ANALYSIS.md) | Análisis de tasa de falsas alarmas por detector / False alarm rate per detector |

---

## Demo Pública / Public Demo

**Panel en vivo / Live panel:**
`https://userf8a2c4.github.io/centinel-engine/panel/`

**Reporte PDF más reciente / Latest PDF report:**
`https://userf8a2c4.github.io/centinel-engine/reports/latest.pdf`

---

## Indicadores Clave / Key Indicators

| Indicador / Indicator | Valor / Value |
|---|---|
| Detectores estadísticos activos / Active detectors | 24 |
| Tests automatizados / Automated tests | ~95 archivos, ~499 passing |
| Cobertura de seguridad / Security coverage | RT-01..RT-15 cerrados / closed |
| Score auditoría de seguridad / Security audit score | 9.9/10 |
| Licencia / License | AGPL-3.0 (anti-fork clause) |
| Lenguaje / Language | Python 3.10+ |
| Dependencias externas / External dependencies | Ninguna propietaria / None proprietary |
| Tiempo de detección / Detection latency | < 5 minutos en elecciones en vivo / < 5 min live |

---

## Contexto de Honduras / Honduras Context

- **Elecciones generales 2025:** 96 archivos JSON de resultados, 18 departamentos, ~2.5M votos
- **Institución aliada / Partner institution:** Universidad Pedagógica Nacional Francisco Morazán (UPNFM)
- **Marco legal / Legal framework:** Constitución de Honduras Art. 3, Ley Electoral y de las Organizaciones Políticas
- **Relevancia:** Honduras es el único país de Centroamérica con un sistema de auditoría electoral open-source operativo

---

## Para Revisores Técnicos / For Technical Reviewers

```bash
# Clonar y ejecutar en 3 comandos / Clone and run in 3 commands
git clone https://github.com/userf8a2c4/centinel-engine
cd centinel-engine
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
