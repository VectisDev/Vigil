# COMPLIANCE.md — Vigil Alignment with International Standards

> **Modalidad: Alineamiento documentado — no certificación formal.**
>
> Este documento traza qué componentes de Vigil se alinean con qué cláusulas de qué norma, con referencia al archivo de código o documentación correspondiente. No implica auditoría independiente ni certificación de conformidad. Está destinado a revisores externos (OEA, Carter Center, NDI, UPNFM, OTF) que necesiten evaluar el rigor técnico del sistema.

---

## Índice de normas cubiertas

| Norma | Título abreviado | Alineamiento estimado |
|---|---|---|
| ISO/IEC 27037:2012 | Identificación y preservación de evidencia digital | ~80% |
| ISO/IEC 27042:2015 | Análisis e interpretación de evidencia digital | ~70% |
| ISO/IEC 27005:2018 | Gestión de riesgos de seguridad de la información | ~40% |
| ISO/IEC 25010:2011 | Calidad de producto software (SQuaRE) | ~60% |
| ISO/IEC 40500:2012 / WCAG 2.2 AA | Accesibilidad de contenido web | ~55% |
| ISO 8601:2019 | Representación de fechas y horas | ✅ completo |
| ISO 690:2021 | Referencias bibliográficas y citas | ✅ completo |
| NIST SP 800-53 Rev 5 | Controles de seguridad y privacidad | ~50% |
| NIST SP 800-92 | Guía para gestión de logs de seguridad | ~70% |

---

## 1. ISO/IEC 27037:2012 — Evidencia digital: identificación, recopilación, adquisición y preservación

**Alineamiento: ~80%**

ISO 27037 define principios para que la evidencia digital sea admisible, relevante, suficiente y fiable ante organismos de revisión.

| Cláusula 27037 | Requisito | Componente Vigil | Archivo | Estado |
|---|---|---|---|---|
| 5.1 — Principios | Relevancia, fiabilidad, suficiencia de la evidencia | Hash chain SHA-256 + Ed25519 encadenado | `src/centinel/core/hashchain.py`, `centinel_engine/hash_chain.py` | ✅ Alineado |
| 5.2 — Identificación | Identificar fuente, origen y contexto de datos | Metadatos de snap: `url`, `ts_fetch`, `snap_index`, `source_hash` | `src/centinel/core/models.py` | ✅ Alineado |
| 5.3 — Recopilación | No alterar datos originales; registro de acceso | `download_and_hash.py` graba hash antes de cualquier transformación | `scripts/download_and_hash.py` | ✅ Alineado |
| 5.4 — Adquisición | Copia forense verificable; hash de integridad | SHA-256 + OTS (Bitcoin timestamp); respaldo cifrado AES-256-GCM | `centinel_engine/secure_backup.py`, `src/centinel/core/anchoring.py` | ✅ Alineado |
| 5.5 — Preservación | Inmutabilidad; cadena de custodia documentada | Hash chain encadenado; modo read-only en snapshots consolidados | `src/centinel/core/hashchain.py`, `docs/architecture/PRE-CAPTURE-CUSTODY-MODEL.md` | ✅ Alineado |
| 6.1 — Documentación | Registro de quién, cuándo, qué acción sobre evidencia | `custody.py`; timestamps de renderización en `/lab/` y `/replay/` | `src/centinel/core/custody.py`, `web/lab/index.html` (render-clock) | ⚠️ Parcial — custodia de operador no registrada en artefacto externo |
| 6.2 — Cadena de custodia | Transferencia de evidencia con registro de responsable | Arquitectura citizen-observer: no hay transferencia física | — | ⚠️ Gap — modelo de custodia es distribuido, no jerárquico |
| 7 — Competencia del personal | Formación del analista | Fuera del alcance de código | `docs/operations/WITNESS-SETUP-DETAILED.md` | ⚠️ Documentado parcialmente |

**Brechas conocidas:**
- 27037 §6.2 asume cadena de custodia centralizada (investigador → fiscal). Vigil es un sistema ciudadano distribuido; la cadena es la verificabilidad criptográfica pública, no una transferencia institucional. Esto es una diferencia de modelo, no un defecto técnico.

---

## 2. ISO/IEC 27042:2015 — Análisis e interpretación de evidencia digital

**Alineamiento: ~70%**

27042 cubre cómo se analiza e interpreta la evidencia una vez preservada, incluyendo reproducibilidad y documentación de métodos.

| Cláusula 27042 | Requisito | Componente Vigil | Archivo | Estado |
|---|---|---|---|---|
| 5.1 — Reproducibilidad | El análisis debe ser replicable por terceros | Reglas engine 100% determinista; dataset público CNE | `src/centinel/core/anomaly_detector.py`, `config/prod/rules_core.yaml` | ✅ Alineado |
| 5.2 — Validación del método | Método analítico documentado y validado | `docs/methodology/crs.md`; 526 tests pytest | `tests/`, `docs/methodology/crs.md` | ✅ Alineado |
| 5.3 — Incertidumbre | Reconocer limitaciones del análisis | Disclaimer permanente en `/lab/` y `/replay/`: "no constituye prueba estadística formal" | `web/lab/index.html`, `web/replay/index.html` | ✅ Alineado |
| 6.1 — Análisis de datos | Proceso sistemático documentado | Rules engine modular (23+ reglas, categorías A–E) | `src/centinel/core/anomaly_detector.py` | ✅ Alineado |
| 6.2 — Interpretación | Distinguir correlación de causalidad | CRS es "indicador operacional" explícitamente, no afirma causalidad | `docs/methodology/crs.md §What this is` | ✅ Alineado |
| 7 — Informe | Formato de reporte; comunicación de hallazgos | PDF forense (ReportLab); `/replay/` snapshot-por-snapshot | `web/replay/index.html`, PDF generation | ⚠️ Parcial — informe PDF no está en producción estable |
| 8 — Competencia analítica | El analista debe poder justificar el método | Colaboración con Prof. Devis Alvarado (UPNFM) en proceso | `docs/legal/EMAIL_DEVIS_DRAFT.md`, `docs/legal/MOU_UPNFM_DRAFT.md` | ⚠️ Pendiente de firma MOU |

**Brechas conocidas:**
- Informe forense PDF está en desarrollo; no está en producción para observación en tiempo real.
- Calibración empírica (HND 2017/2021) pendiente — afecta la defensibilidad de los umbrales CRS ante un perito.

---

## 3. ISO/IEC 27005:2018 — Gestión de riesgos de seguridad de la información

**Alineamiento: ~40%**

27005 requiere un proceso formal y documentado de identificación, análisis, evaluación y tratamiento de riesgos.

| Cláusula 27005 | Requisito | Componente Vigil | Archivo | Estado |
|---|---|---|---|---|
| 7 — Establecer contexto | Definir alcance y criterios de riesgo | VIGIL opera sobre fuentes públicas; scope documentado | `docs/legal/LEGAL-AND-OPERATIONAL-BOUNDARIES.md` | ⚠️ Parcial |
| 8 — Evaluación del riesgo | Identificar activos, amenazas, vulnerabilidades | Threat model implícito (DDoS, hash tamper, CDN poisoning) | `src/centinel/core/anomaly_detector.py` (reglas Cat E) | ⚠️ No formalizado en registro de riesgos |
| 9 — Tratamiento del riesgo | Controles para cada riesgo identificado | Rate limiting, TLS pinning, OTS, secure backup | `centinel_engine/rate_limiter.py`, `centinel_engine/secure_backup.py` | ✅ Controles existentes |
| 10 — Aceptación del riesgo | Riesgos residuales documentados y aceptados | `docs/legal/LEGAL-COMPLIANCE-MATRIX.md` incluye "Riesgo residual" | `docs/legal/LEGAL-COMPLIANCE-MATRIX.md` | ⚠️ Parcial — no cubre todos los activos |
| 11 — Comunicación | Plan de comunicación de riesgos | No existe plan formal | — | ❌ Brecha |
| 12 — Monitoreo | Revisión periódica del perfil de riesgo | Vital signs + alertas continuas | `centinel_engine/vital_signs.py` | ⚠️ Técnico, no formal |

**Brechas conocidas:**
- No existe un registro formal de riesgos (risk register) en formato ISO 27005. Los controles existen en el código, pero no están mapeados a un asset inventory formal.
- Recomendación: crear `docs/compliance/RISK_REGISTER.md` mínimo antes de presentar a OEA/Carter Center.

---

## 4. ISO/IEC 25010:2011 — Calidad de producto software (SQuaRE)

**Alineamiento: ~60%**

25010 define ocho características de calidad: funcionalidad, rendimiento, compatibilidad, usabilidad, fiabilidad, seguridad, mantenibilidad y portabilidad.

| Característica 25010 | Subcaracterística | Componente Vigil | Evidencia | Estado |
|---|---|---|---|---|
| Funcionalidad — Completitud | Cubre todas las funciones requeridas | 23+ reglas de detección activas | `config/prod/rules_core.yaml` | ✅ |
| Funcionalidad — Corrección | Produce resultados correctos | 526 tests; pytest CI | `tests/`, `.github/workflows/` | ✅ |
| Fiabilidad — Tolerancia a fallos | Degradación controlada ante errores | Kill-switch automático; modo crítico | `src/centinel/core/kill_switch.py` | ✅ |
| Fiabilidad — Disponibilidad | Uptime durante observación | Mirror nodes P2P; GitHub Pages CDN | `docs/architecture/RESILIENCE.md` | ✅ |
| Seguridad — Confidencialidad | Protección de datos sensibles | No se procesan datos personales (PII-free) | `docs/legal/LEGAL-COMPLIANCE-MATRIX.md` | ✅ |
| Seguridad — Integridad | Integridad de datos verificable | SHA-256 + Ed25519 + OTS | `centinel_engine/hash_chain.py` | ✅ |
| Seguridad — No repudio | Evidencia de acciones pasadas | Bitcoin anchoring timestamp | `src/centinel/core/anchoring.py` | ✅ |
| Mantenibilidad — Modularidad | Bajo acoplamiento entre módulos | Rules engine plugin-style; separación rules/UI | `config/prod/rules_core.yaml`, `src/centinel/` | ✅ |
| Mantenibilidad — Testabilidad | Facilidad de prueba | 526 tests; cobertura rules engine | `tests/` | ✅ |
| Usabilidad — Operabilidad | Fácil de operar sin entrenamiento | Modo Fácil / Modo Completo en `/ops/` | `web/ops/index.html` | ✅ |
| Usabilidad — Accesibilidad | Accesible a usuarios con discapacidades | WCAG 2.2 AA (ver sección 5) | `web/lab/index.html`, `web/replay/index.html` | ⚠️ Parcial |
| Rendimiento — Eficiencia temporal | Respuesta en tiempo razonable | Polling ≤5 min; UI sin backend | `centinel_engine/scheduler.py` | ✅ |
| Portabilidad — Adaptabilidad | Despliegue en distintos entornos | Zero-cost stack; GitHub Pages + Python | `docs/COST_ELIMINATION_ROADMAP.md` | ✅ |
| Compatibilidad — Interoperabilidad | Integración con sistemas externos | JSON estándar; API pública CNE | `docs/api/API.md` | ⚠️ Solo lectura hacia CNE |

---

## 5. ISO/IEC 40500:2012 / WCAG 2.2 AA — Accesibilidad de contenido web

**Alineamiento: ~55%**

WCAG 2.2 AA es el estándar de facto para accesibilidad web exigido por instituciones internacionales y gobiernos.

| Criterio WCAG 2.2 | Nivel | Componente Vigil | Implementación | Estado |
|---|---|---|---|---|
| 1.1.1 Contenido no textual | A | Gráficos Chart.js | `aria-label` en canvas (parcial) | ⚠️ Parcial |
| 1.4.1 Uso del color | AA | CRS heat zones en `/lab/` y `/replay/` | Redundancia de puntos (1/2/3 dots por severidad) en `crsBandsPlugin` | ✅ Alineado |
| 1.4.3 Contraste mínimo 4.5:1 | AA | Texto sobre fondo `--bg:#080b0f` | Variables CSS del sistema SpaceX; colores revisados | ⚠️ No auditado formalmente |
| 1.4.4 Cambiar tamaño de texto | AA | UI general | Layout CSS; no usa `px` para tamaño de fuente base | ⚠️ Parcial |
| 1.4.11 Contraste de componentes no texto | AA | Botones, bordes, badges | `--border:#1e2530` sobre `--panel:#0d1117` | ⚠️ No auditado formalmente |
| 2.1.1 Teclado | A | Controles del panel | Formularios HTML nativos | ⚠️ Parcial — shortcuts JS no documentados |
| 2.4.3 Orden de foco | A | Navegación tab | Orden DOM estándar | ⚠️ No verificado |
| 3.1.1 Idioma de la página | A | HTML `lang` attribute | `<html lang="es">` | ✅ |
| 4.1.2 Nombre, rol, valor | A | Elementos interactivos | Elementos HTML semánticos | ⚠️ Algunos controles custom sin ARIA |

**Logro clave (criterio 1.4.1):**
El criterio más crítico para los gráficos es 1.4.1: "Color alone is not used as the only visual means of conveying information." El sistema de puntos redundantes en `crsBandsPlugin` (1 punto = ámbar, 2 = naranja, 3 = rojo) satisface este criterio de forma deliberada y documentada.

**Brechas conocidas:**
- Auditoría formal de contraste (ej. con axe-core o Lighthouse) no ejecutada aún.
- Los gráficos Chart.js no tienen texto alternativo estructurado para lectores de pantalla.
- Recomendación: ejecutar `npx axe-cli` sobre `/lab/` y `/replay/` antes de presentación institucional.

---

## 6. ISO 8601:2019 — Representación de fechas y horas

**Alineamiento: ✅ Completo**

| Contexto | Formato usado | Ejemplo | Archivo |
|---|---|---|---|
| Timestamps de snapshots | `YYYY-MM-DDTHH:MM:SSZ` | `2025-11-27T14:30:00Z` | `src/centinel/core/models.py` |
| Render timestamps en UI | `YYYY-MM-DD HH:MM UTC` | `2026-06-23 14:30 UTC` | `web/lab/index.html` (`_updateAcadPanel()`) |
| Nombres de archivos de diary | `YYYYMMDD` | `dev-diary-20260623-...` | `docs/dev-diary/` |
| Logs de operaciones | ISO 8601 extended | `2026-06-23T14:30:00.000Z` | `centinel_engine/vital_signs.py` |

---

## 7. ISO 690:2021 — Información y documentación: citas y referencias bibliográficas

**Alineamiento: ✅ Completo**

Las referencias académicas en documentación técnica siguen el formato ISO 690 (equivalente a la mayoría de estilos de citación académica):

| Documento | Referencias incluidas | Estado |
|---|---|---|
| `docs/methodology/crs.md` | Fisher (1925), contexto estadístico | ✅ |
| `docs/mathematics/statistical-tests.md` | Referencias estadísticas formales | ✅ |
| `docs/mathematics/benford-analysis.md` | Benford (1938), Nigrini et al. | ✅ |
| `docs/grants/OTF_ConceptNote_IFF2026.md` | Referencias a estándares OEA/Carter Center | ✅ |

---

## 8. NIST SP 800-53 Rev 5 — Controles de seguridad y privacidad

**Alineamiento: ~50%**

NIST 800-53 es el catálogo de referencia de controles de seguridad para sistemas de información. Se aplican las familias más relevantes para Vigil.

| Familia | Control | Implementación Vigil | Archivo | Estado |
|---|---|---|---|---|
| AU — Auditoría | AU-2 Generación de eventos de auditoría | Logs de cada fetch + hash en cadena | `centinel_engine/vital_signs.py`, `scripts/download_and_hash.py` | ✅ |
| AU — Auditoría | AU-9 Protección de información de auditoría | Hash chain inmutable; OTS Bitcoin | `src/centinel/core/anchoring.py` | ✅ |
| AU — Auditoría | AU-10 No repudio | Ed25519 + Bitcoin anchoring | `src/centinel/core/anchoring.py` | ✅ |
| SC — Comunicaciones | SC-8 Confidencialidad e integridad en transmisión | TLS + cert pinning | `centinel_engine/proxy_manager.py` | ✅ |
| SC — Comunicaciones | SC-28 Protección de datos en reposo | AES-256-GCM en backups | `centinel_engine/secure_backup.py` | ✅ |
| SI — Integridad del sistema | SI-7 Integridad de software y firmware | SHA-256 por snapshot; binary tamper detection | `src/centinel/core/hashchain.py` | ✅ |
| SI — Integridad del sistema | SI-3 Protección de código malicioso | No aplica directamente (sistema de observación) | — | N/A |
| CP — Contingencia | CP-9 Respaldo del sistema | Backups cifrados automáticos; mirror P2P | `centinel_engine/secure_backup.py`, `docs/architecture/RESILIENCE.md` | ✅ |
| CP — Contingencia | CP-10 Recuperación | Kill-switch; auto-doctor; endpoint healer | `src/centinel/core/kill_switch.py`, `centinel_engine/electoral_authority_healer.py` | ✅ |
| RA — Evaluación de riesgos | RA-3 Evaluación de riesgos | No existe registro formal de riesgos | — | ❌ Brecha |
| PL — Planificación | PL-1 Políticas y procedimientos | Principios operativos documentados | `docs/legal/OPERATING-PRINCIPLES.md` | ⚠️ Parcial |
| SA — Adquisición de sistemas | SA-11 Pruebas de seguridad del desarrollador | 526 tests pytest; CI automático | `tests/`, `.github/workflows/` | ✅ |
| AC — Control de acceso | AC-2 Gestión de cuentas | Auth PBKDF2 + Zero Trust para operadores | `web/ops/index.html` (AUTH IIFE), `docs/dev-diary/dev-diary-20260520-PBKDF2ZeroTrustNoSupabase-01.md` | ✅ |

**Brechas principales:**
- RA-3: Sin risk register formal documentado.
- PL: Políticas de seguridad parciales; no cubren todos los escenarios de respuesta a incidentes.

---

## 9. NIST SP 800-92 — Guía para gestión de logs de seguridad

**Alineamiento: ~70%**

| Sección 800-92 | Requisito | Implementación Vigil | Archivo | Estado |
|---|---|---|---|---|
| 2.1 — Contenido de logs | Timestamp, fuente, evento, resultado | Cada snap incluye: `ts_fetch`, `url`, `snap_index`, hash previo y actual | `src/centinel/core/models.py` | ✅ |
| 2.2 — Consistencia de timestamps | Usar zona horaria estándar (UTC) | Todos los timestamps en UTC/ISO 8601 | `centinel_engine/vital_signs.py` | ✅ |
| 2.3 — Protección de logs | Integridad e inmutabilidad | Hash chain encadenado; no se puede modificar sin romper cadena | `src/centinel/core/hashchain.py` | ✅ |
| 2.4 — Retención | Política de retención definida | Snapshots consolidados en GitHub (inmutables via OTS) | `docs/operations/EVIDENCE-PUBLICATION-SLA.md` | ⚠️ Sin política formal de expiración |
| 3.1 — Centralización | Agregación de logs de múltiples fuentes | Logs de polling centralizados en pipeline | `centinel_engine/vital_signs.py` | ✅ |
| 3.2 — Análisis | Correlación y detección de anomalías | Rules engine (23+ reglas) sobre logs | `src/centinel/core/anomaly_detector.py` | ✅ |
| 4.1 — Revisión | Revisión periódica de logs | Vital signs + alertas automáticas | `centinel_engine/vital_signs.py` | ⚠️ Automático, no revisión manual periódica |
| 4.2 — Reportes | Generación de reportes de actividad | PDF forense; `/replay/` timeline | `web/replay/index.html` | ⚠️ PDF en desarrollo |

---

## Resumen de brechas y recomendaciones

| Brecha | Norma afectada | Prioridad | Acción recomendada |
|---|---|---|---|
| No existe risk register formal | ISO 27005, NIST 800-53 RA-3 | Alta | Crear `docs/compliance/RISK_REGISTER.md` antes de presentación a OEA |
| Calibración CRS pendiente (HND 2017/2021) | ISO 27042 §7 (informe defensible) | Alta | Priorizar con Prof. Alvarado; ver `docs/legal/EMAIL_DEVIS_DRAFT.md` |
| Informe PDF forense no en producción estable | ISO 27042 §7 | Media | Estabilizar generación PDF antes de misión de observación |
| Auditoría formal WCAG (axe-core/Lighthouse) no ejecutada | WCAG 2.2 AA §1.4.3, §1.4.11 | Media | Ejecutar `npx axe-cli` sobre `/lab/` y `/replay/` |
| Texto alternativo en gráficos Chart.js | WCAG 2.2 AA §1.1.1 | Media | Agregar `aria-label` descriptivos a elementos `<canvas>` |
| Cadena de custodia centralizada no implementable | ISO 27037 §6.2 | Baja — diferencia de modelo | Documentar explícitamente el modelo de custodia distribuida en `docs/architecture/` |
| Política formal de seguridad (PL-1) | NIST 800-53 | Baja | Expandir `docs/legal/OPERATING-PRINCIPLES.md` |

---

## Declaración de limitaciones

Este documento **no constituye ni reemplaza**:
- Una auditoría de conformidad realizada por un organismo acreditado.
- Una certificación ISO formal.
- Una opinión legal.
- Una afirmación de que Vigil cumple íntegramente con cualquiera de las normas listadas.

El propósito es demostrar que Vigil fue diseñado con conciencia de estos estándares internacionales y que sus componentes se alinean técnicamente con sus principios centrales, en el nivel de recursos y alcance de un proyecto de sociedad civil de código abierto.

---

*Última actualización: 2026-06-23. Mantenido por el equipo técnico de Vigil / VectisDev.*
*Revisión académica pendiente: Prof. Devis Alvarado, UPNFM — ver `docs/legal/MOU_UPNFM_DRAFT.md`.*
