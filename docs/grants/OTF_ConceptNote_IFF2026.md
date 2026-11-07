# OTF Internet Freedom Fund — IFF-2026-06
## VIGIL Concept Note
*(anteriormente conocido como CENTINEL)*

**Convocatoria:** Open Technology Fund — Internet Freedom Fund  
**Referencia:** IFF-2026-06  
**Fecha de preparación:** 2026-06-07  
**Solicitante:** VectisDev — Lead developer, VIGIL Project  
**Estado:** Borrador — listo para completar formulario online en otf.opentech.fund

---

> **Nota de uso:** Este documento contiene las respuestas preparadas para cada campo del formulario OTF IFF-2026-06. Copiar cada sección directamente al campo correspondiente. El documento también sirve como referencia del posicionamiento estratégico de VIGIL ante fondos de internet freedom.

---

## CAMPO 1 — Título del proyecto

**VIGIL — Protección Criptográfica del Acceso a Información Electoral**

---

## CAMPO 2 — Describe tu proyecto en 1-3 oraciones

En Honduras y Centroamérica, un portal oficial puede publicar un JSON, cambiarlo después, o dejar de responder, y un tercero no tiene un registro propio. **VIGIL** guarda lo que ese portal publicó, cuando el pipeline está corriendo, y deja que otra persona compruebe los bytes sin pedir permiso. La muestra de Honduras 2025 no es esa cadena en vivo: son 64 archivos guardados a mano. La ficha está en `docs/evidence/HN2025.md`. `verify_chain.py` sale en 1 (63 huérfanos). Una tasa de 39,15 actas por minuto es cerca de 3.9× una heurística de 10; no es un estudio pre-registrado.

---

## CAMPO 3 — ¿Qué problema abordará? ¿Cómo fortalece la libertad en Internet?

En elecciones de entornos con instituciones débiles, los organismos electorales controlan el flujo de información con asimetría total: publican datos cuando quieren, en el formato que quieren, y pueden alterar o suprimir publicaciones sin dejar rastro verificable. Periodistas que cubren elecciones en Honduras, Guatemala o Nicaragua no tienen herramientas para demostrar, con evidencia criptográfica verificable por terceros, que un dato cambió después de ser publicado, que hubo una brecha prolongada de publicación/captura, o que la velocidad observada de procesamiento de actas supera el umbral operativo documentado (sujeto a calibración).

Esta asimetría de información reduce la verificabilidad del proceso y silencia a quienes intentan reportarlo: sin evidencia técnica, las denuncias son tratadas como opiniones políticas. VIGIL elimina esta asimetría. Usando exclusivamente datos que el propio Estado publica, genera prueba criptográfica de integridad que cualquier periodista, defensor de derechos u observador puede verificar de forma independiente, offline y sin acreditación institucional alguna.

Sobre los 64 JSON de Honduras 2025, lo reproducible sin red es `make replay-offline` (`docs/VERIFY.md`): el verificador sale en 1 y la raíz Merkle coincide. Los huecos entre nombres de archivo no están medidos como caídas del portal, porque no hay registro de intentos. La tasa de 39.15 actas por minuto es cerca de 3.9× la heurística de 10 del código. Cualquier persona con Python 3.11 puede repetir esa comprobación. El análisis estadístico más pesado es otro comando y necesita dependencias; no es el comando de un minuto.

---

## CAMPO 4 — Si se financia, ¿qué forma adoptará?

**Marcar:** ☑ Desarrollo tecnológico  ☑ Investigación aplicada

El financiamiento se destinaría a: (1) una revisión estadística independiente, todavía no contratada; (2) un intento de calibración con series que no sean la de 2025, o un resultado negativo escrito si esas series no se pueden archivar; (3) guías que repiten `docs/VERIFY.md`; (4) notas de adaptación a un segundo portal público, sin viaje.

---

## CAMPO 5 — Descripción general de actividades

**Actividad 1 — Validación académica (meses 1-4):** Publicar working paper con metodología de las 23 reglas estadísticas en colaboración con an independent academic reviewer. Someter a revisión por pares en *Electoral Studies* o *PLOS One*.

**Actividad 2 — Calibración o resultado negativo:** Buscar series públicas anteriores a 2025. Si se archivan, publicar la distribución de la misma heurística. Si no, publicar que no se encontraron. No se presenta la muestra de 2025 como calibración cerrada.

**Actividad 3 — Guías:** Materiales en español cuyo comando es el de `docs/VERIFY.md`, el mismo que corre CI.

**Actividad 4 — Segundo portal, en escritorio:** Notas de adaptación del esquema JSON de un portal público más. Sin viaje y sin afirmar un piloto de campo.

**Actividad 5 — Release comprobable:** El mantenedor ejecuta el workflow de `docs/operations/RELEASE.md` (tarball, SBOM, SHA256SUMS, firma keyless). Este repositorio no publica el tag solo.

---

## CAMPO 6 — ¿Existen proyectos similares? ¿En qué se diferencia VIGIL?

Existen herramientas de observación electoral de NDI (DemTools), IFES y organismos regionales, pero ninguna comparte las propiedades fundamentales de VIGIL:

- **Sin servidores propios en este pedido:** la comprobación offline corre en un portátil. Operar un nodo de captura sí gasta minutos de CI y tiempo de una persona; eso no es "costo cero".

- **Verificabilidad:** `verify/verify_chain.py` no tiene dependencias. Sale en 0 solo si cada archivo después del primero trae el hash del anterior. En la muestra de 2025 sale en 1. La comprobación positiva de esos bytes es la raíz Merkle, documentada en `docs/VERIFY.md`.

- **Resistencia a la censura:** El diseño de swarm federado (P2P) garantiza que no existe un punto central que una autoridad pueda presionar, bloquear o capturar. El código fuente, bajo licencia AGPL-3.0, no puede ser privatizado.

- **Operación sin acreditación:** Un periodista freelance sin acreditación oficial puede operar VIGIL y generar evidencia técnicamente equivalente a la de un observador institucional.

---

## CAMPO 7 — ¿Cuánto tiempo durará?

**12 meses.** El núcleo ya corre en CI. El financiamiento paga la ficha de evidencia, una revisión estadística independiente todavía no contratada, el detector de caídas basado en intentos registrados (no en la muestra de 2025), materiales que repiten los mismos comandos, y la coordinación. El detalle está en `docs/grants/BUDGET_NARRATIVE.md`.

---

## CAMPO 8 — ¿Cuánto financiamiento necesita? (USD)

**75,000 USD durante 12 meses.** La misma tabla está en `docs/grants/BUDGET_NARRATIVE.md`. No hay un segundo total en este repositorio.

| Hito | USD |
|------|-----|
| Revisión estadística independiente, aún no contratada, o un resultado negativo escrito si la serie histórica no se puede archivar | 22,000 |
| Revisión de seguridad, release firmado y SBOM (el mantenedor publica el tag; el workflow ya está) | 15,000 |
| Detector de caídas = intentos fallidos con marca de tiempo, para la próxima ventana en vivo | 10,000 |
| Materiales en español que repiten `docs/VERIFY.md` | 12,000 |
| Notas de adaptación a un segundo portal público, sin viaje | 8,000 |
| Coordinación y contingencia | 8,000 |
| **Total** | **75,000** |

---

## CAMPO 9 — ¿Quiénes son los usuarios?

**Usuarios directos:** Periodistas de investigación que cubren elecciones en Honduras, Guatemala, El Salvador y Nicaragua — especialmente freelancers y medios independientes sin recursos para observación institucional. Defensores de derechos humanos y activistas de sociedad civil que monitorean procesos electorales en contextos de alta presión política.

**Usuarios técnicos:** Observadores de misiones internacionales (OEA, Carter Center, UE) que necesitan herramientas independientes de verificación. Académicos de estadística electoral y ciencias políticas.

**Beneficiarios indirectos:** Cualquier ciudadano de los países cubiertos cuyo derecho al voto puede ser mejor protegido cuando una alteración de datos posterior a la publicación es técnicamente detectable y verificable. La sola existencia de un sistema de auditoría continuo y verificable genera disuasión.

---

## CAMPO 10 — ¿Dónde están los usuarios?

**Marcar:** ☑ Central America  ☑ Caribbean (como secundario)

América Central (audiencia primaria): Honduras, Guatemala, El Salvador, Nicaragua.  
México y Colombia (audiencia secundaria).  
Global: misiones OEA, UE, Carter Center (observadores internacionales).

> **Nota estratégica:** No marcar todo el mundo. OTF penaliza las propuestas demasiado amplias.

---

## CAMPO 11 — ¿Por qué ustedes son las personas correctas?

El equipo ha demostrado capacidad técnica real, no solo teórica: el motor forense de VIGIL fue aplicado retroactivamente sobre 64 archivos JSON originales del CNE de las elecciones hondureñas del 30/11/2025, detectando automáticamente hallazgos estadísticos reproducibles por cualquier tercero con los mismos archivos públicos.

**Capacidad técnica:** El código es AGPL-3.0. El job `tests` de `.github/workflows/ci.yml` es la prueba; este documento no congela un conteo de tests. La muestra de 2025 se comprueba con `make replay-offline`, no con una cadena que esos archivos no tienen.

**Revisión académica:** Se busca y no está contratada. No hay coautoría institucional.

**Autoría:** VectisDev, seudónimo. La identidad legal no está en este repositorio.

---

## Documentos de soporte disponibles para adjuntar

| Documento | Ruta en repo |
|-----------|-------------|
| Metodología estadística | `docs/research/METHODOLOGY.md` |
| Convenciones estadísticas unificadas | `docs/stats/STATISTICAL_CONVENTIONS.md` |
| Análisis de falsos positivos | `docs/research/FALSE_POSITIVE_ANALYSIS.md` |
| Verificador de cadena de hashes | `verify/verify_chain.py` |
| Revisión de seguridad | `docs/security/SECURITY-REVIEW.md` |
| Teoría del cambio | `docs/architecture/THEORY_OF_CHANGE.md` |
| Budget narrative | `docs/grants/BUDGET_NARRATIVE.md` |

---

*VIGIL — AGPL-3.0 — github.com/VectisDev/Vigil (repositorio aún bajo el nombre histórico VIGIL; migración de nombre en curso)*  
*Documento preparado por el equipo VIGIL · Junio 2026*
