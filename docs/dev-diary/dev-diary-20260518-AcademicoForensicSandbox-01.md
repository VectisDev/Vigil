# Dev Diary - 202605 - AcademicoForensicSandbox - 01

**Fecha aproximada / Approximate date:** 18-may-2026 / May 18, 2026  
**Fase / Phase:** Hacer el argumento forense demostrable sin instalación / Making the forensic argument demonstrable without installation  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v11)  
**Rama / Branch:** dev-v11  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-OneCommandBootstrap-01.md`. El sistema recolectaba, hasheaba y publicaba evidencia, pero no había forma de mostrar la detección a alguien sin Python. / The system collected, hashed, and published evidence, but there was no way to show detection to someone without Python.

---

## [ES]

### 1) El Problema (Contexto)
El análisis forense de CENTINEL vivía enterrado en código Python que requería instalación, ambiente configurado y conocimiento técnico para ejecutar. Un observador electoral, un periodista de datos o un evaluador de NDI no podía ver los 25 detectores en acción sin primero instalar dependencias y entender la estructura del proyecto. En la práctica, me di cuenta de que el argumento forense no existía para el 95% de las personas que necesitaban verlo: existía solo para quienes lo construimos.

### 2) La Hipótesis
Un sandbox completamente en el navegador, calibrado con datos reales de Honduras 2025 y con inyección adversarial controlada, puede convertir el argumento técnico en uno visual y accesible. Si alguien puede inyectar fraude con un clic y ver cómo el sistema lo detecta en tiempo real, el argumento se vuelve autoexplicativo. No requiere Python, no requiere instalación, no requiere que nadie confíe en una promesa.

### 3) El Experimento / Implementación
Construí `web/academico/` de cero: una simulación adversarial de 30 días y 2880 snapshots con una matriz de inyección A/B/C que modela timing (cuándo aparece la anomalía), magnitude (qué tan grande es el desvío) y frequency (qué tan a menudo ocurre). Calibré las 25 reglas de detección a los datos reales de HN-2025 con los pesos partidarios de PN, LIBRE y PSH. La interfaz incluye velocidades de playback 1x/10x/100x/500x, toggle de loop, y export a PNG y PDF sin ningún CDN externo. Los colores partidarios son los oficiales verificados.

### 4) El Resultado (La Lección)
Funcionó. Los 25 detectores son observables en tiempo real desde cualquier navegador moderno, sin instalar nada. La calibración a datos reales de Honduras 2025 hace que el argumento sea específico y concreto — no una demo genérica de "detección de anomalías" sino una demostración de qué habría detectado el sistema en la elección de 2025. Ese nivel de especificidad es lo que convierte una demo técnica en un argumento político.

### 5) La Decisión Final (Takeaway)
El sandbox forense ES el argumento ante audiencias sin Python. Si no puedo mostrar la detección ocurriendo en datos reales del contexto específico, el argumento técnico no existe para quien toma decisiones de financiamiento o cobertura. La herramienta de demostración no es un accesorio del sistema: es una parte igual de crítica que el sistema mismo.

### 6) Qué cambió y por qué ahora
Construí `web/academico/` de cero porque los financiadores institucionales (NDI, Carter Center, #StartSmall) necesitan ver el sistema en acción, no leer código. Un grant no se aprueba sobre la base de una promesa técnica; se aprueba cuando quien evalúa puede reproducir el resultado. El sandbox es ese artefacto reproducible — abre el link, inyecta fraude, ve la detección. Eso es un argumento de grant, no marketing.

### 7) Decisiones de implementación
- **Sin CDN externo:** zero-trust por diseño; el sandbox funciona en redes restrictivas o sin internet, lo cual importa en el contexto de elecciones en entornos de censura.
- **Calibración real, no inventada:** los pesos PN/LIBRE/PSH vienen de datos verificables de HN-2025, no de valores ficticios. Eso hace el argumento atacable y verificable, no solo creíble.
- **Inyección reproducible:** seed fija para que dos personas que corren la misma demo vean exactamente el mismo resultado. La reproducibilidad es un argumento de integridad.
- **Export sin backend:** PNG y PDF se generan en el cliente. No hay servidor que pueda fallar, no hay datos que salgan del navegador.
- **Velocidades de playback:** 1x para análisis, 500x para demostrar que el sistema cubre un mes de conteo en segundos.

### 8) Impacto
Un evaluador de NDI, Carter Center o #StartSmall puede abrir el sandbox, configurar la inyección A/B/C, hacer play y observar los 25 detectores respondiendo — todo en menos de 2 minutos, sin instalar nada. Eso transforma la propuesta de un documento de texto con afirmaciones técnicas en una experiencia verificable. Para el argumento de financiamiento, esa diferencia es determinante.

### 9) Aprendizaje de ciclo
Me di cuenta de que la democratización del argumento forense es tan urgente como el argumento mismo. Un sistema que solo los técnicos pueden entender es un sistema que solo los técnicos pueden defender — y los técnicos no son quienes aprueban grants, escriben las coberturas periodísticas o movilizan a los observadores. La accesibilidad del argumento no es UX: es una condición de impacto.

---

## [EN]

### 1) The Problem (Context)
CENTINEL's forensic analysis lived buried inside Python code that required installation, a configured environment, and technical knowledge to run. An electoral observer, a data journalist, or an NDI evaluator could not see the 25 detectors in action without first installing dependencies and understanding the project structure. In practice, I realized the forensic argument did not exist for 95% of the people who needed to see it — it existed only for those who built it.

### 2) The Hypothesis
A fully browser-based sandbox, calibrated with real Honduras 2025 data and controlled adversarial injection, can turn the technical argument into a visual, accessible one. If someone can inject fraud with one click and watch the system detect it in real time, the argument becomes self-explanatory. No Python, no installation, no requirement that anyone trust a promise.

### 3) The Experiment / Implementation
I built `web/academico/` from scratch: an adversarial simulation of 30 days and 2,880 snapshots with an A/B/C injection matrix modeling timing (when the anomaly appears), magnitude (how large the deviation is), and frequency (how often it occurs). I calibrated the 25 detection rules against real HN-2025 data with the partisan weights of PN, LIBRE, and PSH. The interface includes playback speeds of 1x/10x/100x/500x, loop toggle, and PNG/PDF export with no external CDN. Partisan colors are the verified official ones.

### 4) The Result (The Lesson)
It worked. All 25 detectors are observable in real time from any modern browser, with nothing to install. Calibration to real Honduras 2025 data makes the argument specific and concrete — not a generic "anomaly detection" demo but a demonstration of what the system would have detected in the 2025 election. That level of specificity is what turns a technical demo into a political argument.

### 5) The Final Decision (Takeaway)
The forensic sandbox IS the argument for audiences without Python. If I cannot show detection happening on real data from the specific context, the technical argument does not exist for the people who make funding or coverage decisions. The demonstration tool is not an accessory to the system — it is an equally critical part of it.

### 6) What changed and why now
I built `web/academico/` from scratch because institutional funders (NDI, Carter Center, #StartSmall) need to see the system in action, not read code. A grant is not approved on the basis of a technical promise — it is approved when the evaluator can reproduce the result. The sandbox is that reproducible artifact: open the link, inject fraud, see detection. That is a grant argument, not marketing.

### 7) Implementation choices
- **No external CDN:** zero-trust by design; the sandbox works on restrictive networks or offline, which matters in censorship-context election environments.
- **Real calibration, not invented:** PN/LIBRE/PSH weights come from verifiable HN-2025 data, not fictional values. That makes the argument attackable and verifiable, not just credible.
- **Reproducible injection:** fixed seed so two people running the same demo see exactly the same result. Reproducibility is an integrity argument.
- **Client-side export:** PNG and PDF are generated in the browser. No server that can fail, no data leaving the browser.
- **Playback speeds:** 1x for analysis, 500x to demonstrate the system covers a month-long count in seconds.

### 8) Impact
An NDI, Carter Center, or #StartSmall evaluator can open the sandbox, configure the A/B/C injection, hit play, and observe 25 detectors responding — all in under 2 minutes, with nothing installed. That transforms the proposal from a text document with technical claims into a verifiable experience. For the funding argument, that difference is decisive.

### 9) Cycle takeaway
I realized that democratizing the forensic argument is as urgent as the argument itself. A system only technicians can understand is a system only technicians can defend — and technicians are not the ones who approve grants, write coverage, or mobilize observers. The accessibility of the argument is not UX: it is a condition of impact.

---

## Cierre / Close
El sandbox forense cierra la última brecha entre "el sistema funciona" y "cualquier persona puede verlo funcionar" — esa brecha era tan importante como cualquier feature técnica del motor. / The forensic sandbox closes the last gap between "the system works" and "anyone can see it work" — that gap mattered as much as any technical feature of the engine.
