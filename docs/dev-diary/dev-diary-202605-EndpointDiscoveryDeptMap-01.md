# Dev Diary - 202605 - EndpointDiscoveryDeptMap - 01

**Fecha aproximada / Approximate date:** 20-may-2026 / May 20, 2026  
**Fase / Phase:** Hacer la validación de endpoint resistente a cambios de URL y a servidores falsos / Making endpoint validation resistant to URL changes and fake servers  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-ForkUxSetupWizard-01.md`. Con el onboarding resuelto, el siguiente punto débil era la detección del endpoint electoral correcto cuando las URLs del CNE cambian entre ciclos o cuando un adversario controla la infraestructura de red. / With onboarding resolved, the next weak point was detecting the correct electoral endpoint when CNE URLs change between cycles or when an adversary controls network infrastructure.

---

## [ES]

### 1) El Problema (Contexto)
Las URLs del CNE de Honduras cambian entre ciclos electorales sin aviso previo, y la validación de endpoint en CENTINEL solo verificaba conectividad HTTP: si el servidor respondía 200 OK, el endpoint era considerado válido. Esa lógica tiene una falla estructural: cualquier servidor puede responder 200 OK. Un adversario que controla DNS, un proxy de intercepción, o un espejo no autorizado puede responder 200 OK con contenido fabricado o vacío y pasar la validación. El sistema podía estar recolectando evidencia del servidor equivocado sin ningún mecanismo de detección.

### 2) La Hipótesis
Si se valida el contenido HTML del endpoint — buscando tokens específicamente electorales como nombres de partidos, códigos de mesa, o términos del dominio electoral hondureño — en lugar de solo la conectividad HTTP, el sistema puede rechazar servidores que responden 200 pero no sirven contenido electoral real. Complementado con un fallback Playwright para páginas JavaScript-rendered, un mapa canónico de códigos de departamento (00-18 para los 18 departamentos de Honduras), y validación de la estructura numérica de las URLs, esto cierra los falsos positivos.

### 3) El Experimento / Implementación
`endpoint_discovery.py` fue extendido con cuatro capas adicionales de validación: (1) análisis de contenido HTML que busca tokens electorales específicos del dominio hondureño en el cuerpo de la respuesta, (2) fallback a Playwright para páginas que requieren JavaScript para renderizar contenido electoral, (3) el mapa `DEPT_CODES` con los 18 códigos de departamento de Honduras (00-18) como constante canónica verificable, y (4) validación de segmentos numéricos en las URLs como heurística de legitimidad. El wizard de setup fue actualizado para incluir el paso de configuración de URL con estas validaciones integradas.

### 4) El Resultado (La Lección)
Funcionó. El sistema ahora rechaza endpoints que responden 200 pero no contienen contenido electoral verificable. El mapa `DEPT_CODES` 00-18 es la primera representación verificable de la geografía hondureña integrada al motor de CENTINEL — no como dato de display sino como constante operacional que afecta la lógica de validación. La validación de estructura de URL detecta patrones numéricos que son una huella de los sistemas de gestión electoral del CNE.

### 5) La Decisión Final (Takeaway)
El formato de URL y el contenido de la respuesta son huellas de legitimidad tan importantes como cualquier certificado SSL o IP autorizada. Un adversario sofisticado puede obtener un certificado válido y responder desde una IP legítima con contenido falso o vacío. La única defensa contra eso es validar que lo que se recibe es lo que se esperaba recibir — contenido electoral real del CNE, no solo una respuesta HTTP exitosa.

### 6) Qué cambió y por qué ahora
La validación fue reforzada porque el modelo de amenaza de un conteo electoral incluye adversarios con capacidad de controlar infraestructura de red, redirigir DNS, o servir espejos no autorizados. Si CENTINEL recolecta evidencia durante 30 días apuntando al servidor equivocado, toda la cadena de custodia está comprometida — no porque los hashes sean incorrectos, sino porque los datos que se hashearon no son los datos del CNE. La integridad de la fuente es tan crítica como la integridad del contenido.

### 7) Decisiones de implementación
- **Contenido-primero, no conectividad-primero:** la validación de HTTP 200 es necesaria pero no suficiente. La validación de contenido es la capa que distingue el endpoint correcto de un servidor equivocado.
- **Playwright como fallback, no como primario:** Playwright es más lento y requiere dependencias adicionales. Se usa solo cuando la validación de contenido HTML puro falla — lo que indica una página JS-rendered que requiere ejecución de JavaScript para mostrar el contenido electoral.
- **`DEPT_CODES` como constante canónica:** los 18 códigos (00-18) son verificables externamente contra la estructura administrativa de Honduras. Eso hace la constante atacable y auditable, no solo funcional.
- **Validación numérica de URL como heurística:** los sistemas de gestión electoral del CNE usan segmentos numéricos en sus URLs de forma consistente. Un endpoint que no sigue ese patrón es sospechoso aunque responda correctamente.

### 8) Impacto
El sistema puede ahora detectar si está apuntando al endpoint equivocado antes de recolectar una sola pieza de evidencia. Eso es una garantía estructural de integridad en la cadena de custodia: la validación de fuente ocurre antes de que la evidencia exista, no después de que ya está hasheada en la cadena.

### 9) Aprendizaje de ciclo
La validación de fuente es tan crítica como la validación de integridad. No basta verificar que los datos no fueron alterados en tránsito; hay que verificar que vienen del lugar correcto. Un hash perfecto de datos del servidor equivocado es evidencia comprometida con apariencia de integridad. El adversario más sofisticado no altera los datos: sirve datos distintos desde el lugar correcto.

---

## [EN]

### 1) The Problem (Context)
Honduras CNE URLs change between electoral cycles without prior notice, and CENTINEL's endpoint validation only checked HTTP connectivity: if the server responded 200 OK, the endpoint was considered valid. That logic has a structural flaw: any server can respond 200 OK. An adversary who controls DNS, an interception proxy, or an unauthorized mirror can respond 200 OK with fabricated or empty content and pass validation. The system could be collecting evidence from the wrong server with no detection mechanism.

### 2) The Hypothesis
If the HTML content of the endpoint is validated — looking for specifically electoral tokens like party names, ballot codes, or Honduran electoral domain terms — rather than just HTTP connectivity, the system can reject servers that respond 200 but do not serve real electoral content. Complemented by a Playwright fallback for JavaScript-rendered pages, a canonical map of department codes (00-18 for Honduras's 18 departments), and validation of the numerical structure of URLs, this closes the false positives.

### 3) The Experiment / Implementation
`endpoint_discovery.py` was extended with four additional validation layers: (1) HTML content analysis looking for electoral tokens specific to the Honduran domain in the response body, (2) Playwright fallback for pages requiring JavaScript to render electoral content, (3) the `DEPT_CODES` map with all 18 Honduras department codes (00-18) as a verifiable canonical constant, and (4) validation of numerical segments in URLs as a legitimacy heuristic. The setup wizard was updated to include the URL configuration step with these validations integrated.

### 4) The Result (The Lesson)
It worked. The system now rejects endpoints that respond 200 but do not contain verifiable electoral content. The `DEPT_CODES` 00-18 map is the first verifiable representation of Honduran geography integrated into the CENTINEL engine — not as display data but as an operational constant that affects validation logic. URL structure validation detects numerical patterns that are a fingerprint of CNE electoral management systems.

### 5) The Final Decision (Takeaway)
URL format and response content are legitimacy fingerprints as important as any SSL certificate or authorized IP. A sophisticated adversary can obtain a valid certificate and respond from a legitimate IP with false or empty content. The only defense against that is validating that what is received is what was expected to be received — real CNE electoral content, not just a successful HTTP response.

### 6) What changed and why now
Validation was hardened because the threat model for an electoral count includes adversaries with the capacity to control network infrastructure, redirect DNS, or serve unauthorized mirrors. If CENTINEL collects evidence for 30 days pointing at the wrong server, the entire chain of custody is compromised — not because the hashes are incorrect, but because the data that was hashed is not the CNE's data. Source integrity is as critical as content integrity.

### 7) Implementation choices
- **Content-first, not connectivity-first:** HTTP 200 validation is necessary but not sufficient. Content validation is the layer that distinguishes the correct endpoint from the wrong server.
- **Playwright as fallback, not primary:** Playwright is slower and requires additional dependencies. It is used only when plain HTML content validation fails — indicating a JS-rendered page requiring JavaScript execution to display electoral content.
- **`DEPT_CODES` as canonical constant:** the 18 codes (00-18) are externally verifiable against Honduras's administrative structure. That makes the constant attackable and auditable, not just functional.
- **URL numerical validation as heuristic:** CNE electoral management systems use numerical segments in their URLs consistently. An endpoint that does not follow that pattern is suspicious even if it responds correctly.

### 8) Impact
The system can now detect if it is pointing at the wrong endpoint before collecting a single piece of evidence. That is a structural integrity guarantee for the chain of custody: source validation occurs before evidence exists, not after it is already hashed into the chain.

### 9) Cycle takeaway
Source validation is as critical as integrity validation. It is not enough to verify that data was not altered in transit; it is necessary to verify that it came from the right place. A perfect hash of data from the wrong server is compromised evidence with the appearance of integrity. The most sophisticated adversary does not alter data: they serve different data from the right address.

---

## Cierre / Close
Validar conectividad era la respuesta fácil; validar que el contenido es electoral es la respuesta correcta — porque en un conteo disputado, la diferencia entre las dos puede ser toda la evidencia. / Validating connectivity was the easy answer; validating that the content is electoral is the correct answer — because in a disputed count, the difference between the two can be all the evidence.
