# OTF Internet Freedom Fund — IFF-2026-06
## CENTINEL Concept Note

**Convocatoria:** Open Technology Fund — Internet Freedom Fund  
**Referencia:** IFF-2026-06  
**Fecha de preparación:** 2026-06-07  
**Solicitante:** Carlos Zelaya — Desarrollador Principal CENTINEL  
**Patrocinador institucional:** IGETEL S.A. (en negociación)  
**Estado:** Borrador — listo para completar formulario online en otf.opentech.fund

---

> **Nota de uso:** Este documento contiene las respuestas preparadas para cada campo del formulario OTF IFF-2026-06. Copiar cada sección directamente al campo correspondiente. El documento también sirve como referencia del posicionamiento estratégico de CENTINEL ante fondos de internet freedom.

---

## CAMPO 1 — Título del proyecto

**CENTINEL — Protección Criptográfica del Acceso a Información Electoral**

---

## CAMPO 2 — Describe tu proyecto en 1-3 oraciones

En Honduras y Centroamérica, los datos electorales oficiales pueden ser publicados, alterados o suprimidos sin que periodistas, activistas ni ciudadanos tengan forma de detectarlo. **CENTINEL** es un sistema de software libre que captura, encadena criptográficamente y somete a 23 pruebas estadísticas y forenses cada publicación del organismo electoral — en tiempo real, a costo cero, sin depender de ninguna autoridad. En el análisis forense retroactivo sobre archivos JSON originales del CNE de las elecciones hondureñas de 2025, detectó automáticamente un apagón de 13 horas de datos y una tasa de resolución matemáticamente imposible de 39 actas por minuto.

---

## CAMPO 3 — ¿Qué problema abordará? ¿Cómo fortalece la libertad en Internet?

En elecciones de entornos con instituciones débiles, los organismos electorales controlan el flujo de información con asimetría total: publican datos cuando quieren, en el formato que quieren, y pueden alterar o suprimir publicaciones sin dejar rastro verificable. Periodistas que cubren elecciones en Honduras, Guatemala o Nicaragua no tienen herramientas para demostrar, con evidencia matemáticamente irrefutable, que un dato cambió después de ser publicado, que hubo un apagón de información deliberado, o que la velocidad de procesamiento de actas es físicamente imposible.

Esta asimetría de información protege a actores que manipulan el proceso y silencia a quienes intentan reportarlo: sin evidencia técnica, las denuncias son tratadas como opiniones políticas. CENTINEL elimina esta asimetría. Usando exclusivamente datos que el propio Estado publica, genera prueba criptográfica de integridad que cualquier periodista, defensor de derechos u observador puede verificar de forma independiente, offline y sin acreditación institucional alguna.

En el análisis forense retroactivo sobre 64 archivos JSON originales del CNE de las elecciones hondureñas del 30 de noviembre de 2025, el motor de CENTINEL detectó automáticamente: 41 brechas de comunicación, incluyendo 6 apagones nocturnos de más de 10 horas; y una tasa de resolución de 39.15 actas por minuto — 4 veces el límite físico plausible. Cualquier periodista puede reproducir estos hallazgos con un solo comando, usando los mismos archivos originales del CNE. CENTINEL no requiere infraestructura propia, no genera costos operativos y puede ser desplegado en cualquier país de la región.

---

## CAMPO 4 — Si se financia, ¿qué forma adoptará?

**Marcar:** ☑ Desarrollo tecnológico  ☑ Investigación aplicada

El financiamiento se destinaría a: (1) validación académica independiente con la Universidad Pedagógica Nacional Francisco Morazán (UPNFM); (2) expansión del motor estadístico con calibración contra datos históricos de Honduras; (3) guías técnicas para periodistas y observadores internacionales; (4) piloto de campo en Guatemala y El Salvador.

---

## CAMPO 5 — Descripción general de actividades

**Actividad 1 — Validación académica (meses 1-4):** Publicar working paper con metodología de las 23 reglas estadísticas en colaboración con Prof. Devis Alvarado (UPNFM). Someter a revisión por pares en *Electoral Studies* o *PLOS One*.

**Actividad 2 — Calibración con datos hondureños reales (meses 2-5):** Ajustar los 23 umbrales estadísticos usando series históricas del CNE 2013-2025. Eliminar umbrales arbitrarios e implementar calibración departamental.

**Actividad 3 — Guías para periodistas y observadores (meses 3-6):** Producir documentación técnica accesible en español para periodistas de investigación y observadores electorales de Centroamérica. Incluir tutoriales de verificación independiente con `verify_chain.py`.

**Actividad 4 — Expansión regional (meses 4-8):** Despliegue de análisis retroactivo en Guatemala (TSE) y El Salvador (TSE), con configuraciones de país y pruebas coordinadas con organizaciones de la sociedad civil locales.

**Actividad 5 — Documentación internacional (meses 6-8):** Preparar materiales para presentación ante OEA y Carter Center. Mapeo de cumplimiento contra estándares internacionales de observación electoral.

---

## CAMPO 6 — ¿Existen proyectos similares? ¿En qué se diferencia CENTINEL?

Existen herramientas de observación electoral de NDI (DemTools), IFES y organismos regionales, pero ninguna comparte las propiedades fundamentales de CENTINEL:

- **Costo cero:** DemTools y sistemas similares requieren servidores, personal técnico y presupuesto. CENTINEL opera exclusivamente en la capa gratuita de GitHub. Cualquier periodista puede operar una instancia sin presupuesto.

- **Verificabilidad criptográfica:** Ninguna herramienta conocida genera una cadena SHA-256 encadenada verificable offline por terceros. CENTINEL incluye `verify_chain.py`, un script de 0 dependencias que cualquier persona puede usar para verificar la integridad de todos los datos capturados.

- **Resistencia a la censura:** El diseño de swarm federado (P2P) garantiza que no existe un punto central que una autoridad pueda presionar, bloquear o capturar. El código fuente, bajo licencia AGPL-3.0, no puede ser privatizado.

- **Operación sin acreditación:** Un periodista freelance sin acreditación oficial puede operar CENTINEL y generar evidencia técnicamente equivalente a la de un observador institucional.

---

## CAMPO 7 — ¿Cuánto tiempo durará?

**6 meses a 1 año.** El núcleo técnico ya está construido y validado retroactivamente. El financiamiento acelera la validación académica independiente, la expansión regional y la producción de materiales para usuarios finales.

---

## CAMPO 8 — ¿Cuánto financiamiento necesita? (USD)

**$75,000 USD**

| Rubro | Monto |
|-------|-------|
| Validación académica y publicación | $15,000 |
| Calibración estadística con datos históricos | $10,000 |
| Guías técnicas y materiales para periodistas | $12,000 |
| Piloto regional Guatemala/El Salvador | $20,000 |
| Documentación internacional (OEA/Carter Center) | $10,000 |
| Contingencia y coordinación | $8,000 |
| **Infraestructura operativa** | **$0** (GitHub free tier) |
| **Total** | **$75,000** |

---

## CAMPO 9 — ¿Quiénes son los usuarios?

**Usuarios directos:** Periodistas de investigación que cubren elecciones en Honduras, Guatemala, El Salvador y Nicaragua — especialmente freelancers y medios independientes sin recursos para observación institucional. Defensores de derechos humanos y activistas de sociedad civil que monitorean procesos electorales en contextos de alta presión política.

**Usuarios técnicos:** Observadores de misiones internacionales (OEA, Carter Center, UE) que necesitan herramientas independientes de verificación. Académicos de estadística electoral y ciencias políticas.

**Beneficiarios indirectos:** Cualquier ciudadano de los países cubiertos cuyo derecho al voto puede ser mejor protegido cuando la manipulación de datos es técnicamente detectable y demostrable. La sola existencia de un sistema de auditoría en tiempo real genera disuasión.

---

## CAMPO 10 — ¿Dónde están los usuarios?

**Marcar:** ☑ Central America  ☑ Caribbean (como secundario)

América Central (audiencia primaria): Honduras, Guatemala, El Salvador, Nicaragua.  
México y Colombia (audiencia secundaria).  
Global: misiones OEA, UE, Carter Center (observadores internacionales).

> **Nota estratégica:** No marcar todo el mundo. OTF penaliza las propuestas demasiado amplias.

---

## CAMPO 11 — ¿Por qué ustedes son las personas correctas?

El equipo ha demostrado capacidad técnica real, no solo teórica: el motor forense de CENTINEL fue aplicado retroactivamente sobre 64 archivos JSON originales del CNE de las elecciones hondureñas del 30/11/2025, detectando automáticamente hallazgos estadísticos reproducibles por cualquier tercero con los mismos archivos públicos.

**Capacidad técnica:** El motor de 23 reglas estadísticas y forenses está implementado, documentado y cuenta con 526 tests automatizados. La arquitectura criptográfica (SHA-256 encadenado, Ed25519, PBKDF2) ha sido revisada internamente. El código es completamente abierto bajo licencia AGPL-3.0.

**Respaldo académico:** Colaboración iniciada con el Prof. Devis Alvarado, investigador de la Universidad Pedagógica Nacional Francisco Morazán (UPNFM), para validación estadística independiente de la metodología.

**Respaldo institucional hondureño:** IGETEL S.A. (Ingeniería en Telecomunicaciones y Sistemas, parte del Grupo ITEL de Centroamérica) identificada como organización patrocinadora — empresa líder en telecomunicaciones e ingeniería tecnológica en Honduras con más de 20 años de operación regional.

**Contexto local irreemplazable:** El equipo opera desde Honduras, con conocimiento directo del contexto electoral centroamericano, los patrones históricos del CNE y las necesidades reales de los periodistas y observadores locales.

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

*CENTINEL — AGPL-3.0 — github.com/vectisdev/centinel*  
*Documento preparado por el equipo CENTINEL · Junio 2026*
