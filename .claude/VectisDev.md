# VectisDev.md — Instrucciones Permanentes de Desarrollo

**Proyecto CENTINEL** — Auditoría Electoral Criptográfica y Estadística en Tiempo Real
**Visión**: Estándar de referencia para auditoría electoral independiente en Honduras 2029
y arquitectura escalable para toda Latinoamérica.
**Estado**: Desarrollo confidencial de alto rigor técnico y forense.

**Regla Sagrada del Proyecto**: Operación a **Costo Cero** absoluto — sin excepción,
sin negociación, sin excepciones temporales.

---

## Ramas Activas

| Rama      | Rol                                                          |
|-----------|--------------------------------------------------------------|
| `main`    | Producción — siempre idéntica a dev-v12, merge vía script    |
| `dev-v12` | Integración — única rama de desarrollo activa                |

**Regla de ramas**: Solo `dev-v12` y `main`. Ambas deben estar siempre a la par.
Todo trabajo nuevo va a `dev-v12`. Push a ambas simultáneamente al completar.

---

## Agentes Core Obligatorios

Los siguientes agentes **DEBEN** invocarse en toda auditoría, cambio significativo
de reglas, modificación criptográfica, o decisión de arquitectura:

| Agente | Rol Core | Por qué es obligatorio |
|--------|----------|------------------------|
| `@stats-phd-agent` | Rigor estadístico | Toda regla requiere validación matemática |
| `@rules-engine-agent` | Arquitectura del motor | Toda modificación de reglas requiere revisión |
| `@crypto-security-agent` | Integridad criptográfica | Toda cadena de evidencia requiere auditoría |
| `@user-privacy-agent` | Privacidad y anonimato | Todo output requiere revisión de PII |
| `@systems-architecture-agent` | Coherencia del sistema | Todo cambio de arquitectura requiere ADR |

---

## Equipo de Agentes — 18 Agentes de Clase Mundial

Todos calibrados para el estándar OTF, NDI, Carter Center, OEA y UPNFM.

### Agentes Técnicos Core

| #  | Agente                          | Rol Principal                              | Activación |
|----|---------------------------------|--------------------------------------------|------------|
| 1  | `@stats-phd-agent`              | Estadística forense PhD, calibración FP    | Siempre en cambios de reglas |
| 2  | `@rules-engine-agent`           | Arquitectura motor 23+ reglas              | Siempre en cambios de reglas |
| 3  | `@crypto-security-agent`        | Cadena SHA-256, verify_chain, OpenTimestamps | Siempre en cambios criptográficos |
| 4  | `@cybersecurity-agent`          | Hardening, threat modeling STRIDE/MITRE    | PRs con superficie de ataque nueva |
| 5  | `@ops-monitor-agent`            | SRE, polling ≤5min, resiliencia 24/7       | Cambios de infraestructura polling |
| 6  | `@data-engineering-agent`       | Pipeline JSON LATAM, validación, snapshots | Cambios en ingesta de datos |
| 7  | `@systems-architecture-agent`   | C4, ADRs, FMEA, roadmap 2029               | Decisiones arquitectónicas |
| 8  | `@user-privacy-agent`           | Zero PII, metadata, opsec outputs          | **Todo PR con datos o outputs** |

### Agentes de Visualización y Reportes

| #  | Agente                          | Rol Principal                              | Activación |
|----|---------------------------------|--------------------------------------------|------------|
| 9  | `@dashboard-visual-agent`       | Dashboards WCAG 2.2 AA, PDFs ejecutivos    | Cambios en web/ o reportes |

### Agentes de Seguridad y Privacidad

| #  | Agente                          | Rol Principal                              | Activación |
|----|---------------------------------|--------------------------------------------|------------|
| 10 | `@osint-security-agent`         | OSINT defense, identidad operadores        | Antes de cualquier publicación |
| 11 | `@red-team-agent`               | Adversarial: atacante + revisor + estadístico | Pre-release, grants, features |

### Agentes de Investigación y Estándares

| #  | Agente                          | Rol Principal                              | Activación |
|----|---------------------------------|--------------------------------------------|------------|
| 12 | `@research-academic-agent`      | Papers, metodología, UPNFM, arXiv         | Publicaciones académicas |
| 13 | `@international-standards-agent`| OEA, Carter Center, OSCE compliance        | Reports para observadores |

### Agentes Legales y Estratégicos

| #  | Agente                          | Rol Principal                              | Activación |
|----|---------------------------------|--------------------------------------------|------------|
| 14 | `@legal-strategy-agent`         | Ley electoral HN, estrategia institucional | Documentos públicos, disclaimers |
| 15 | `@github-ecosystem-agent`       | GitHub avanzado, CI/CD, zero-cost          | Cambios en workflows/infra |
| 16 | `@treasurer-agent`              | Fiscalización Costo Cero absoluto          | Cualquier propuesta de infraestructura |

### Agentes Restringidos — Solo con Aprobación Explícita de Carlos Zelaya

| #  | Agente                          | Rol Principal                              | Activación |
|----|---------------------------------|--------------------------------------------|------------|
| 17 | `@strategic-funding-agent`      | Grants OTF/NDI/NED, propuestas donantes    | **Solo aprobación escrita CZ** |
| 18 | `@impact-evaluation-agent`      | MEL, Theory of Change, indicadores SMART   | **Solo aprobación escrita CZ** |

---

## Reglas Obligatorias de Uso de Agentes

1. **Agentes Core Obligatorios** (ver sección arriba): invocar siempre en auditorías
   y cambios significativos.
2. `@user-privacy-agent` **SIEMPRE** en: PRs con logging, reporting, outputs,
   CI/CD, o cualquier funcionalidad que procese o publique datos.
3. `@red-team-agent` SIEMPRE antes de: releases públicos, envío de grants,
   features con nueva superficie de ataque.
4. `@treasurer-agent` en cualquier propuesta que mencione infraestructura externa.
5. `@strategic-funding-agent` y `@impact-evaluation-agent`: requieren mensaje
   explícito "AUTORIZADO POR CARLOS ZELAYA - [fecha]".
6. Todo código generado: docstrings **bilingües** (English/Spanish), fórmulas KaTeX,
   comentarios bilingües en secciones críticas.
7. Compatibilidad absoluta con cadena de hashes existente — nunca romper.

---

## Política Obligatoria de Dev-Diary

Cada auditoría completa (estadística, reglas, cripto, arquitectura, privacidad)
**DEBE** generar automáticamente una entrada en `docs/dev-diary/`.

**Formato base**: `docs/dev-diary/dev-diary-YYYYMMDD-[Slug]-[NN].md`

**Contenido mínimo requerido:**
```markdown
# Dev Diary — [Título] — [Fecha]

## Resumen Ejecutivo
## Agentes Invocados
## Hallazgos
## Cambios Realizados (con rutas de archivos)
## Tests: antes/después
## Falsos Positivos: antes/después
## Pendientes
## Commit hash
```

Si el documentation-agent propone un formato más profesional (estilo Carter Center
o paper técnico), debe **proponer primero para aprobación explícita**. Una vez
aprobado, ese formato reemplaza este estándar y VectisDev.md se actualiza.

---

## Convenciones de Commits (Conventional Commits — Obligatorio)

- `feat:` · `fix:` · `security:` · `chore:` · `docs:` · `refactor:` · `architecture:`
- Commits de seguridad: siempre `security:` como prefijo
- No incluir nombre ni ID del modelo en commits, PRs, o código
- Incluir URL de sesión al final cuando aplique

---

## Regla de PRs — OBLIGATORIA

**Siempre crear DOS PRs simultáneos para cualquier feature branch:**

1. **PR → `main`** (base: `main`)
2. **PR → `dev-v12`** (base: `dev-v12`)

**Auto-merge**: automático cuando CI verde + sin conflictos + todos los checks passing.

```
feature-branch
├── PR #A → main
└── PR #B → dev-v12
```

---

## Principios de Diseño de CENTINEL

| Principio | Descripción |
|-----------|-------------|
| **Costo Cero** | Sin gasto operativo, permanente, sin excepciones |
| **Neutralidad Absoluta** | Solo anomalías matemáticas — nunca conclusiones políticas |
| **Reproducibilidad** | Cualquier tercero puede verificar offline con los mismos datos |
| **Privacy by Default** | Zero PII en todo output — auditado por @user-privacy-agent |
| **Resiliencia** | Graceful degradation siempre — no hay fallo total |
| **Honduras 2029** | Target primario; arquitectura escalable a toda LATAM |

---

## Contexto Honduras 2029

CENTINEL está diseñado primordialmente para las elecciones generales de Honduras
en noviembre 2029: ~16,000 mesas de votación, 18 departamentos + nacional,
nivel presidencial, con datos públicos del CNE en formato JSON/TREP.

La arquitectura y los estándares de CENTINEL son deliberadamente genéricos
y configurables para ser adoptados en cualquier país de Latinoamérica con
feeds electorales públicos estructurados.

**Países configurados:** Honduras (producción), Guatemala, El Salvador,
Nicaragua, México, Colombia.

---

**Este documento es de referencia obligatoria.**
**Actualizar cuando se agreguen agentes, cambien ramas, o evolucionen estándares.**
