# Dev Diary - 202605 - AutonomousSelfHealingOps - 01

**Fecha aproximada / Approximate date:** 20-may-2026 / May 20, 2026  
**Fase / Phase:** Hacer el sistema capaz de detectar su propio daño y repararse solo / Making the system capable of detecting its own damage and repairing itself  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-EndpointDiscoveryDeptMap-01.md`. Con la validación de fuente resuelta, el siguiente vector de fallo era la corrupción o eliminación de archivos web críticos sin operador disponible para responder. / With source validation resolved, the next failure vector was corruption or deletion of critical web files without an available operator to respond.

---

## [ES]

### 1) El Problema (Contexto)
CENTINEL prometía operación autónoma durante semanas, pero si un archivo web crítico — el panel, el replay, o el academico — era corrompido o eliminado, ya sea por error de configuración, un push incorrecto, o acción deliberada de un adversario con acceso al repositorio, no había ningún mecanismo de detección ni de recuperación automática. Los operadores en campo en Honduras o Venezuela no tienen acceso a consola de servidor, no pueden correr `git restore`, y en el contexto de un conteo disputado, pueden estar en situaciones donde la respuesta inmediata es físicamente imposible. La promesa "autónomo" tenía un asterisco invisible: autónomo excepto cuando los archivos se rompen.

### 2) La Hipótesis
Un healer autónomo que corre en cron diario, detecta archivos críticos faltantes o corruptos, y los restaura desde HEAD sin intervención humana — complementado con alertas push ntfy que notifican al operador antes de que el sistema falle silenciosamente — más documentación AUTONOMOUS-OPERATIONS legible por personas no técnicas, cubre el ciclo completo de fallo y recuperación. El operador es notificado, el sistema se repara, y hay un registro auditable de lo que ocurrió.

### 3) El Experimento / Implementación
Creé `scripts/heal_web.py`: detecta la lista de archivos web críticos, verifica que existen y no están corruptos (tamaño mínimo, estructura básica), y restaura desde HEAD los que fallan la verificación usando `git show HEAD:<path>`. Creé el workflow `heal-web.yml` con cron a las 06:00 UTC diario y dispatch manual para intervención inmediata; incluye modo `--dry-run` para auditoría sin modificaciones. Integré ntfy como canal de alertas push zero-cost y zero-account: el operador recibe una notificación antes de que el healer actúe, y otra confirmando la restauración. Escribí `docs/AUTONOMOUS-OPERATIONS.md` bilingüe orientado a dos audiencias distintas: evaluadores de grants que necesitan entender la garantía operacional, y operadores en campo que necesitan saber qué hacer cuando llega una alerta.

### 4) El Resultado (La Lección)
Funcionó. Los archivos críticos se restauran solos cada 24h como baseline, con capacidad de intervención manual inmediata si el operador recibe una alerta y puede responder. Los operadores reciben notificación push antes de que el sistema falle silenciosamente — lo que significa que la degradación es visible antes de convertirse en una interrupción de servicio. La documentación convierte la promesa "sistema autónomo" en un artefacto demostrable con comportamiento verificable.

### 5) La Decisión Final (Takeaway)
Un sistema que detecta su propio daño, se repara solo, y alerta al operador antes de fallar silenciosamente es cualitativamente diferente de uno que depende de que alguien esté disponible para responder. Esa diferencia importa exactamente en el momento en que el adversario actúa — porque el adversario elige cuándo actuar, y elige el momento de menor disponibilidad del operador. La autonomía operacional tiene que ser un invariante del sistema, no una característica que funciona cuando el operador está disponible.

### 6) Qué cambió y por qué ahora
Construí el healer porque "autónomo" en la propuesta de grant tiene un significado específico: el sistema puede operar sin intervención humana durante semanas en el peor escenario. Ese peor escenario incluye archivos corrompidos, operadores no disponibles, y períodos de alta presión política donde el adversario tiene mayor motivación para interferir. Construir el healer ahora, antes de que sea necesario, es la única forma de garantizar que la promesa de autonomía sea real cuando importe.

### 7) Decisiones de implementación
- **Restauración desde HEAD, no desde backup externo:** zero dependencias externas; el historial de git ES el backup. Eso significa que la restauración funciona exactamente igual en un repositorio recién clonado que en uno con meses de historia.
- **Cron diario como baseline, dispatch manual como escape hatch:** 24h es la ventana máxima de exposición en condiciones normales; el dispatch manual permite respuesta inmediata si el operador recibe una alerta y quiere actuar antes del cron.
- **Modo `--dry-run` por defecto para auditoría:** el healer puede correr en modo lectura — reporta qué restauraría sin modificar nada — lo que permite auditar el estado del sistema sin riesgo de cambios no deseados.
- **ntfy por su modelo zero-cost y zero-account para el receptor:** el operador en campo no necesita crear una cuenta ni pagar nada para recibir alertas push. Solo necesita instalar la app de ntfy y suscribirse al canal configurado.
- **`AUTONOMOUS-OPERATIONS.md` con dos voces distintas:** la sección para evaluadores usa lenguaje de garantías y SLOs; la sección para operadores usa instrucciones paso a paso sin jerga técnica. El mismo documento sirve dos propósitos completamente distintos.

### 8) Impacto
El sistema puede sobrevivir a la indisponibilidad del operador durante 24h con recuperación automática garantizada. Para un conteo electoral que puede durar un mes — como ha ocurrido en Honduras — eso es la diferencia entre una cadena de custodia continua y lagunas en el registro de evidencia. El evaluador de grant puede leer `AUTONOMOUS-OPERATIONS.md` y entender exactamente qué garantiza el sistema y bajo qué condiciones falla.

### 9) Aprendizaje de ciclo
La autonomía operacional no es una feature: es un requisito de misión en contextos donde el operador puede estar imposibilitado de responder por razones que van desde el corte de internet hasta la detención. Diseñar para el operador disponible es diseñar para el escenario fácil. El adversario en un conteo disputado no actúa cuando el operador está disponible — actúa cuando no lo está. El sistema tiene que funcionar en ambos casos.

---

## [EN]

### 1) The Problem (Context)
CENTINEL promised autonomous operation for weeks, but if a critical web file — the panel, the replay, or the academico — was corrupted or deleted, whether by configuration error, an incorrect push, or deliberate action by an adversary with repository access, there was no detection mechanism and no automatic recovery. Field operators in Honduras or Venezuela have no server console access, cannot run `git restore`, and in the context of a disputed count, may be in situations where immediate response is physically impossible. The "autonomous" promise had an invisible asterisk: autonomous except when files break.

### 2) The Hypothesis
An autonomous healer running on a daily cron, detecting missing or corrupted critical files, and restoring them from HEAD without human intervention — complemented by ntfy push alerts that notify the operator before the system fails silently — plus AUTONOMOUS-OPERATIONS documentation readable by non-technical people, covers the complete failure and recovery cycle. The operator is notified, the system repairs itself, and there is an auditable record of what happened.

### 3) The Experiment / Implementation
I created `scripts/heal_web.py`: it detects the list of critical web files, verifies that they exist and are not corrupted (minimum size, basic structure), and restores from HEAD any that fail verification using `git show HEAD:<path>`. I created the `heal-web.yml` workflow with a daily cron at 06:00 UTC and manual dispatch for immediate intervention; it includes `--dry-run` mode for audit without modifications. I integrated ntfy as a zero-cost, zero-account push alert channel: the operator receives a notification before the healer acts, and another confirming the restoration. I wrote `docs/AUTONOMOUS-OPERATIONS.md` bilingually aimed at two distinct audiences: grant evaluators who need to understand the operational guarantee, and field operators who need to know what to do when an alert arrives.

### 4) The Result (The Lesson)
It worked. Critical files are restored automatically every 24h as a baseline, with immediate manual intervention capability if the operator receives an alert and can respond. Operators receive push notification before the system fails silently — meaning degradation is visible before it becomes a service interruption. The documentation turns the "autonomous system" promise into a demonstrable artifact with verifiable behavior.

### 5) The Final Decision (Takeaway)
A system that detects its own damage, repairs itself, and alerts the operator before failing silently is qualitatively different from one that depends on someone being available to respond. That difference matters exactly when the adversary acts — because the adversary chooses when to act, and they choose the moment of least operator availability. Operational autonomy must be a system invariant, not a feature that works when the operator is available.

### 6) What changed and why now
I built the healer because "autonomous" in the grant proposal has a specific meaning: the system can operate without human intervention for weeks in the worst-case scenario. That worst case includes corrupted files, unavailable operators, and periods of high political pressure where the adversary has greater motivation to interfere. Building the healer now, before it is needed, is the only way to guarantee that the autonomy promise is real when it matters.

### 7) Implementation choices
- **Restoration from HEAD, not from external backup:** zero external dependencies; the git history IS the backup. That means restoration works exactly the same in a freshly cloned repository as in one with months of history.
- **Daily cron as baseline, manual dispatch as escape hatch:** 24h is the maximum exposure window under normal conditions; manual dispatch allows immediate response if the operator receives an alert and wants to act before the cron.
- **`--dry-run` mode by default for auditing:** the healer can run in read mode — reporting what it would restore without modifying anything — allowing the system state to be audited without risk of unwanted changes.
- **ntfy for its zero-cost, zero-account receiver model:** the field operator does not need to create an account or pay anything to receive push alerts. They only need to install the ntfy app and subscribe to the configured channel.
- **`AUTONOMOUS-OPERATIONS.md` with two distinct voices:** the evaluator section uses guarantees and SLO language; the operator section uses step-by-step instructions without technical jargon. The same document serves two completely different purposes.

### 8) Impact
The system can survive operator unavailability for 24h with guaranteed automatic recovery. For an electoral count that can last a month — as has happened in Honduras — that is the difference between a continuous chain of custody and gaps in the evidence record. The grant evaluator can read `AUTONOMOUS-OPERATIONS.md` and understand exactly what the system guarantees and under what conditions it fails.

### 9) Cycle takeaway
Operational autonomy is not a feature: it is a mission requirement in contexts where the operator may be unable to respond for reasons ranging from internet cutoff to detention. Designing for the available operator is designing for the easy scenario. The adversary in a disputed count does not act when the operator is available — they act when they are not. The system must work in both cases.

---

## Cierre / Close
Un sistema que se repara solo no elimina al operador — lo libera para que actúe donde un script no puede actuar. / A system that repairs itself does not eliminate the operator — it frees them to act where a script cannot.
