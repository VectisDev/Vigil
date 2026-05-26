# Dev Diary - 202605 - ForkUxSetupWizard - 01

**Fecha aproximada / Approximate date:** 19-may-2026 / May 19, 2026  
**Fase / Phase:** Colapsar la fricción de onboarding para el observador que hace fork / Collapsing onboarding friction for the observer doing the fork  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-ZeroCostStackDataSeparation-01.md`. Con el stack a costo cero, el siguiente cuello de botella era la primera experiencia: fork → configurar → Pages activo. / With the zero-cost stack in place, the next bottleneck was the first-run experience: fork → configure → Pages live.

---

## [ES]

### 1) El Problema (Contexto)
El README de CENTINEL era técnico-primero: asumía que quien lo leía sabía qué es un fork, qué es GitHub Pages, y qué hace un workflow de Actions. Alguien que llegaba como observador electoral — con el objetivo de desplegar vigilancia, no de aprender GitHub — no podía determinar en 30 segundos si el sistema era para ellos y cuáles eran los primeros pasos. El wizard de setup, además, requería pasos manuales para activar Pages y configurar la URL del panel: pasos que un observador local sin experiencia en configuración de repositorios no puede completar solo, y que creaban una barrera invisible justo en el momento de mayor motivación del usuario.

### 2) La Hipótesis
Dos secciones explícitas y diferenciadas en el README — una para el observador que quiere desplegar y una para el desarrollador que quiere contribuir — más un wizard que detecta el estado de Pages, lo activa automáticamente si es necesario, y actualiza el README del fork con el enlace al panel al terminar, eliminan toda ambigüedad en la experiencia de entrada. El resultado del wizard debe ser visible en el README: un enlace activo que prueba que el deploy funcionó.

### 3) El Experimento / Implementación
El README fue rediseñado con una sección guiada en la parte superior dirigida explícitamente a observadores no-técnicos, con pasos numerados y sin jerga. Se creó un SETUP-GUIDE comprensivo y lineal. El wizard (`scripts/setup_wizard.py`) fue extendido para detectar si GitHub Pages está habilitado en el repositorio del usuario, activarlo mediante la API de GitHub si no lo está, y al terminar el setup completo, actualizar el README del fork con el enlace al panel público. El wizard termina con un veredicto claro: panel activo en `[URL]`.

### 4) El Resultado (La Lección)
Funcionó. El flujo fork-to-running es ahora demostrable en una sesión de trabajo sin conocimiento técnico previo de GitHub. El enlace al panel aparece en el README del fork después del wizard — el resultado es visible y verificable, no solo prometido en texto. Eso convierte "cualquier observador puede desplegar esto" de una afirmación en un hecho comprobable.

### 5) La Decisión Final (Takeaway)
La fricción en setup es un riesgo de grant, no un problema de UX. Los evaluadores de NDI, Carter Center y otras organizaciones verifican la replicabilidad del sistema como parte del proceso de due diligence. Un evaluador que no puede completar el setup en 15 minutos extrae la conclusión de que el sistema es demasiado complejo para observadores en campo — aunque el código sea excelente. La primera experiencia ES parte del argumento técnico.

### 6) Qué cambió y por qué ahora
El README y el wizard fueron rediseñados porque la promesa "cualquier observador puede desplegar esto" requería que la experiencia de fork fuera tan guiada y sin fricción como el sistema mismo. No es suficiente que el sistema funcione si el camino para llegar a "funcionando" requiere conocimiento implícito que la mayoría de los usuarios no tiene. La tecnología no puede ser el obstáculo en un proyecto cuya misión es democratizar la vigilancia electoral.

### 7) Decisiones de implementación
- **Sección observador-primero en el README:** quien llega con el objetivo de desplegar ve sus instrucciones antes de cualquier contenido técnico. Los desarrolladores tienen su sección separada debajo.
- **Wizard como única fuente de verdad del setup:** no hay instrucciones duplicadas en diferentes documentos. Si hay una discrepancia, el wizard gana.
- **Auto-activación de Pages sin configuración manual:** el wizard usa la API de GitHub para habilitar Pages en la rama correcta. El usuario no necesita saber que esa configuración existe.
- **Enlace en README como confirmación de éxito:** el wizard no termina con "setup completado" — termina con un enlace activo en el README que cualquiera puede verificar. El éxito es visible, no declarado.
- **SETUP-GUIDE lineal:** cada paso tiene un prerrequisito claro y un resultado verificable. No hay pasos que dependan de conocimiento implícito del usuario.

### 8) Impacto
Un observador electoral en Honduras o Venezuela puede hacer fork del repositorio, correr el wizard con `make wizard`, y tener el panel público activo con el enlace en el README en una sola sesión. Eso convierte la promesa de accesibilidad en un artefacto demostrable: el evaluador de grant puede hacer el proceso completo durante la revisión y verificar el resultado en tiempo real.

### 9) Aprendizaje de ciclo
El onboarding es el primer argumento del sistema. Si el sistema es difícil de desplegar, el mensaje implícito es que está diseñado para técnicos — lo que contradice la misión de un sistema de vigilancia electoral que debe poder ser operado por organizaciones locales con recursos limitados. Cada minuto de fricción en el setup es un argumento en contra del grant y en contra de la adopción real.

---

## [EN]

### 1) The Problem (Context)
CENTINEL's README was technical-first: it assumed that readers knew what a fork was, what GitHub Pages was, and what an Actions workflow does. Someone arriving as an electoral observer — with the goal of deploying oversight, not learning GitHub — could not determine in 30 seconds whether the system was for them and what the first steps were. The setup wizard also required manual steps to activate Pages and configure the panel URL: steps that a local observer without repository configuration experience cannot complete alone, creating an invisible barrier at exactly the moment of highest user motivation.

### 2) The Hypothesis
Two explicit and differentiated sections in the README — one for the observer who wants to deploy and one for the developer who wants to contribute — plus a wizard that detects Pages status, auto-activates it if needed, and updates the fork's README with the panel link when done, eliminate all ambiguity in the entry experience. The wizard's result must be visible in the README: an active link that proves the deploy worked.

### 3) The Experiment / Implementation
The README was redesigned with a guided section at the top directed explicitly at non-technical observers, with numbered steps and no jargon. A comprehensive and linear SETUP-GUIDE was created. The wizard (`scripts/setup_wizard.py`) was extended to detect whether GitHub Pages is enabled in the user's repository, activate it via the GitHub API if not, and upon completing the full setup, update the fork's README with the link to the public panel. The wizard ends with a clear verdict: panel live at `[URL]`.

### 4) The Result (The Lesson)
It worked. The fork-to-running flow is now demonstrable in a single work session with no prior GitHub technical knowledge. The panel link appears in the fork's README after the wizard — the result is visible and verifiable, not just promised in text. That turns "any observer can deploy this" from a claim into a verifiable fact.

### 5) The Final Decision (Takeaway)
Setup friction is a grant risk, not a UX problem. NDI, Carter Center, and other organizational evaluators verify system replicability as part of the due diligence process. An evaluator who cannot complete setup in 15 minutes concludes that the system is too complex for field observers — even if the code is excellent. The first-run experience IS part of the technical argument.

### 6) What changed and why now
The README and wizard were redesigned because the promise "any observer can deploy this" required the fork experience to be as guided and frictionless as the system itself. It is not enough for the system to work if the path to "working" requires implicit knowledge that most users do not have. Technology cannot be the obstacle in a project whose mission is to democratize electoral oversight.

### 7) Implementation choices
- **Observer-first section in the README:** whoever arrives with the goal of deploying sees their instructions before any technical content. Developers have their separate section below.
- **Wizard as single source of truth for setup:** no duplicated instructions across different documents. If there is a discrepancy, the wizard wins.
- **Auto-activation of Pages without manual configuration:** the wizard uses the GitHub API to enable Pages on the correct branch. The user does not need to know that configuration exists.
- **Link in README as success confirmation:** the wizard does not end with "setup complete" — it ends with an active link in the README that anyone can verify. Success is visible, not declared.
- **Linear SETUP-GUIDE:** each step has a clear prerequisite and a verifiable result. No steps depend on the user's implicit knowledge.

### 8) Impact
An electoral observer in Honduras or Venezuela can fork the repository, run the wizard with `make wizard`, and have the public panel live with the link in the README in a single session. That turns the accessibility promise into a demonstrable artifact: the grant evaluator can run the complete process during review and verify the result in real time.

### 9) Cycle takeaway
Onboarding is the system's first argument. If the system is hard to deploy, the implicit message is that it is designed for technicians — which contradicts the mission of an electoral oversight system that must be operable by local organizations with limited resources. Every minute of friction in setup is an argument against the grant and against real adoption.

---

## Cierre / Close
La experiencia de fork no es una página de documentación: es la primera prueba de que la promesa de accesibilidad es real. / The fork experience is not a documentation page: it is the first test of whether the accessibility promise is real.
