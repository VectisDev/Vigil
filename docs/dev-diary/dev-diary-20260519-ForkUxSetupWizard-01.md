# Dev Diary - 202605 - ForkUxSetupWizard - 01

**Fecha aproximada / Approximate date:** 19-may-2026 / May 19, 2026  
**Fase / Phase:** Colapsar la friccion de onboarding para el observador que hace fork / Collapsing onboarding friction for the observer doing the fork  
**Version interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion de `dev-diary-202605-ZeroCostStackDataSeparation-01.md`. Con el stack a costo cero, el siguiente cuello de botella era la primera experiencia: fork -> configurar -> Pages activo. / With the zero-cost stack in place, the next bottleneck was the first-run experience: fork -> configure -> Pages live.

---

## [ES]

### 1) El Problema (Contexto)
El README de CENTINEL era tecnico-primero: asumia que quien lo leia sabia que es un fork, que es GitHub Pages, y que hace un workflow de Actions. Alguien que llegaba como observador electoral -- con el objetivo de desplegar vigilancia, no de aprender GitHub -- no podia determinar en 30 segundos si el sistema era para ellos y cuales eran los primeros pasos. El wizard de setup, ademas, requeria pasos manuales para activar Pages y configurar la URL del panel: pasos que un observador local sin experiencia en configuracion de repositorios no puede completar solo, y que creaban una barrera invisible justo en el momento de mayor motivacion del usuario.

### 2) La Hipotesis
Dos secciones explicitas y diferenciadas en el README -- una para el observador que quiere desplegar y una para el desarrollador que quiere contribuir -- mas un wizard que detecta el estado de Pages, lo activa automaticamente si es necesario, y actualiza el README del fork con el enlace al panel al terminar, eliminan toda ambiguedad en la experiencia de entrada. El resultado del wizard debe ser visible en el README: un enlace activo que prueba que el deploy funciono.

### 3) El Experimento / Implementacion
Redisene el README con una seccion guiada en la parte superior dirigida explicitamente a observadores no-tecnicos, con pasos numerados y sin jerga. Cree un SETUP-GUIDE comprensivo y lineal. Extendi el wizard (`scripts/setup_wizard.py`) para detectar si GitHub Pages esta habilitado en el repositorio del usuario, activarlo mediante la API de GitHub si no lo esta, y al terminar el setup completo, actualizar el README del fork con el enlace al panel publico. El wizard termina con un veredicto claro: panel activo en `[URL]`.

### 4) El Resultado (La Leccion)
Funciono. El flujo fork-to-running es ahora demostrable en una sesion de trabajo sin conocimiento tecnico previo de GitHub. El enlace al panel aparece en el README del fork despues del wizard -- el resultado es visible y verificable, no solo prometido en texto. Eso convierte "cualquier observador puede desplegar esto" de una afirmacion en un hecho comprobable.

### 5) La Decision Final (Takeaway)
La friccion en setup es un riesgo de grant, no un problema de UX. Los evaluadores de NDI, Carter Center y otras organizaciones verifican la replicabilidad del sistema como parte del proceso de due diligence. Un evaluador que no puede completar el setup en 15 minutos extrae la conclusion de que el sistema es demasiado complejo para observadores en campo -- aunque el codigo sea excelente. La primera experiencia ES parte del argumento tecnico.

### 6) Que cambio y por que ahora
Redisene el README y el wizard porque la promesa "cualquier observador puede desplegar esto" requeria que la experiencia de fork fuera tan guiada y sin friccion como el sistema mismo. No es suficiente que el sistema funcione si el camino para llegar a "funcionando" requiere conocimiento implicito que la mayoria de los usuarios no tiene. La tecnologia no puede ser el obstaculo en un proyecto cuya mision es democratizar la vigilancia electoral.

### 7) Decisiones de implementacion
- **Seccion observador-primero en el README:** quien llega con el objetivo de desplegar ve sus instrucciones antes de cualquier contenido tecnico. Los desarrolladores tienen su seccion separada debajo.
- **Wizard como unica fuente de verdad del setup:** no hay instrucciones duplicadas en diferentes documentos. Si hay una discrepancia, el wizard gana.
- **Auto-activacion de Pages sin configuracion manual:** el wizard usa la API de GitHub para habilitar Pages en la rama correcta. El usuario no necesita saber que esa configuracion existe.
- **Enlace en README como confirmacion de exito:** el wizard no termina con "setup completado" -- termina con un enlace activo en el README que cualquiera puede verificar. El exito es visible, no declarado.
- **SETUP-GUIDE lineal:** cada paso tiene un prerrequisito claro y un resultado verificable. No hay pasos que dependan de conocimiento implicito del usuario.

### 8) Impacto
Un observador electoral en Honduras o Venezuela puede hacer fork del repositorio, correr el wizard con `make wizard`, y tener el panel publico activo con el enlace en el README en una sola sesion. Eso convierte la promesa de accesibilidad en un artefacto demostrable: el evaluador de grant puede hacer el proceso completo durante la revision y verificar el resultado en tiempo real.

### 9) Aprendizaje de ciclo
El onboarding es el primer argumento del sistema. Si el sistema es dificil de desplegar, el mensaje implicito es que esta disenado para tecnicos -- lo que contradice la mision de un sistema de vigilancia electoral que debe poder ser operado por organizaciones locales con recursos limitados. Cada minuto de friccion en el setup es un argumento en contra del grant y en contra de la adopcion real.

---

## [EN]

### 1) The Problem (Context)
CENTINEL's README was technical-first: it assumed that readers knew what a fork was, what GitHub Pages was, and what an Actions workflow does. Someone arriving as an electoral observer -- with the goal of deploying oversight, not learning GitHub -- could not determine in 30 seconds whether the system was for them and what the first steps were. The setup wizard also required manual steps to activate Pages and configure the panel URL: steps that a local observer without repository configuration experience cannot complete alone, creating an invisible barrier at exactly the moment of highest user motivation.

### 2) The Hypothesis
Two explicit and differentiated sections in the README -- one for the observer who wants to deploy and one for the developer who wants to contribute -- plus a wizard that detects Pages status, auto-activates it if needed, and updates the fork's README with the panel link when done, eliminate all ambiguity in the entry experience. The wizard's result must be visible in the README: an active link that proves the deploy worked.

### 3) The Experiment / Implementation
I redesigned the README with a guided section at the top directed explicitly at non-technical observers, with numbered steps and no jargon. I created a comprehensive and linear SETUP-GUIDE. I extended the wizard (`scripts/setup_wizard.py`) to detect whether GitHub Pages is enabled in the user's repository, activate it via the GitHub API if not, and upon completing the full setup, update the fork's README with the link to the public panel. The wizard ends with a clear verdict: panel live at `[URL]`.

### 4) The Result (The Lesson)
It worked. The fork-to-running flow is now demonstrable in a single work session with no prior GitHub technical knowledge. The panel link appears in the fork's README after the wizard -- the result is visible and verifiable, not just promised in text. That turns "any observer can deploy this" from a claim into a verifiable fact.

### 5) The Final Decision (Takeaway)
Setup friction is a grant risk, not a UX problem. NDI, Carter Center, and other organizational evaluators verify system replicability as part of the due diligence process. An evaluator who cannot complete setup in 15 minutes concludes that the system is too complex for field observers -- even if the code is excellent. The first-run experience IS part of the technical argument.

### 6) What changed and why now
I redesigned the README and wizard because the promise "any observer can deploy this" required the fork experience to be as guided and frictionless as the system itself. It is not enough for the system to work if the path to "working" requires implicit knowledge that most users do not have. Technology cannot be the obstacle in a project whose mission is to democratize electoral oversight.

### 7) Implementation choices
- **Observer-first section in the README:** whoever arrives with the goal of deploying sees their instructions before any technical content. Developers have their separate section below.
- **Wizard as single source of truth for setup:** no duplicated instructions across different documents. If there is a discrepancy, the wizard wins.
- **Auto-activation of Pages without manual configuration:** the wizard uses the GitHub API to enable Pages on the correct branch. The user does not need to know that configuration exists.
- **Link in README as success confirmation:** the wizard does not end with "setup complete" -- it ends with an active link in the README that anyone can verify. Success is visible, not declared.
- **Linear SETUP-GUIDE:** each step has a clear prerequisite and a verifiable result. No steps depend on the user's implicit knowledge.

### 8) Impact
An electoral observer in Honduras or Venezuela can fork the repository, run the wizard with `make wizard`, and have the public panel live with the link in the README in a single session. That turns the accessibility promise into a demonstrable artifact: the grant evaluator can run the complete process during review and verify the result in real time.

### 9) Cycle takeaway
Onboarding is the system's first argument. If the system is hard to deploy, the implicit message is that it is designed for technicians -- which contradicts the mission of an electoral oversight system that must be operable by local organizations with limited resources. Every minute of friction in setup is an argument against the grant and against real adoption.

---

## Cierre / Close
La experiencia de fork no es una pagina de documentacion: es la primera prueba de que la promesa de accesibilidad es real. / The fork experience is not a documentation page: it is the first test of whether the accessibility promise is real.
