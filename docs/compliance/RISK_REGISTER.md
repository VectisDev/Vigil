# Risk Register — Vigil

> ISO 27005 §8 / NIST SP 800-53 RA-3. Última actualización: 2026-06-23.
> Revisión recomendada: antes de cada observación electoral activa.

## Activos principales

| ID | Activo | Descripción |
|---|---|---|
| A-01 | Hash chain de snapshots | Evidencia criptográfica principal — SHA-256 encadenado |
| A-02 | Clave Ed25519 del operador | Clave de firma de actas — compromiso = pérdida de no repudio |
| A-03 | Pipeline de polling | Proceso que descarga y hashea snaps del CNE |
| A-04 | GitHub Pages (web/) | Interfaz pública para observadores, prensa y ciudadanía |
| A-05 | Configuración de endpoints CNE | URLs y rutas de las fuentes de datos oficiales |
| A-06 | Identidad del operador | Anonimato ante adversarios estatales en Honduras |

## Registro de riesgos

| ID | Activo | Amenaza | Probabilidad | Impacto | Nivel | Control existente | Riesgo residual |
|---|---|---|---|---|---|---|---|
| R-01 | A-01 | Modificación retroactiva de snapshots por adversario | Baja | Crítico | Alto | SHA-256 encadenado + OTS Bitcoin; verify_chain.py público | Bajo — romper la cadena es detectable |
| R-02 | A-02 | Pérdida o robo de clave Ed25519 | Baja | Alto | Alto | Almacenamiento fuera de línea; documentado en WITNESS-SETUP | Medio — sin rotación automática de clave |
| R-03 | A-03 | DDoS contra endpoints CNE | Media | Medio | Medio | Rate limiting token bucket; mirror nodes; modo crítico | Bajo — degradación controlada, no pérdida de datos |
| R-04 | A-03 | Envenenamiento de CDN / caché | Baja | Alto | Medio | Hash-before-process; hash chain detecta alteración | Bajo — alteración post-captura es detectable |
| R-05 | A-04 | Takedown de GitHub Pages | Baja | Alto | Medio | Mirror nodes P2P; IPFS backup; docs en múltiples repos | Medio — restauración requiere intervención manual |
| R-06 | A-05 | Cambio silencioso de endpoints por CNE | Media | Alto | Alto | Endpoint healer; alertas automáticas de cambio de estructura | Medio — ventana de ceguera hasta detección |
| R-07 | A-06 | De-anonimización del operador | Media | Crítico | Alto | Sin PII en código ni logs; OSINT hygiene | Medio — depende de disciplina operativa |
| R-08 | A-01 | Rollback de actas por CNE (retiro de datos ya capturados) | Media | Alto | Alto | Hash chain inalterable; OTS ancla timestamp previo | Bajo — evidencia del estado anterior preservada |
| R-09 | A-03 | Falsos positivos sistemáticos en reglas | Media | Alto | Alto | 526 tests; calibración pendiente HND 2017/2021; disclaimer UI | Medio — calibración empírica pendiente |
| R-10 | A-04 | Uso malintencionado de hallazgos por actores políticos | Media | Alto | Alto | Disclaimer permanente; metodología pública; neutralidad explícita | Medio — fuera del control técnico |

## Tratamiento de riesgos residuales aceptados

| ID | Decisión | Justificación |
|---|---|---|
| R-02 | Aceptado | Rotación de clave requiere re-firma de toda la cadena — diseño futuro |
| R-05 | Aceptado | Zero-cost mandate — sin CDN propio pagado |
| R-07 | Aceptado | Control operativo, no técnico |
| R-09 | Aceptado hasta calibración | Calibración con Prof. Alvarado en proceso |
| R-10 | Aceptado | Fuera del alcance técnico del sistema |

---
*Mantenido por el equipo técnico de Vigil. Ver también: `docs/legal/OPERATING-PRINCIPLES.md`.*
