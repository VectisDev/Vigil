# Dev Diary - 202605 - OneCommandBootstrap - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Colapsar el último escalón de fricción / Collapsing the last friction step  
**Versión interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuación de `dev-diary-202605-MediumGapsHardening-01.md`. TIER 5 dejó "pon el modo, verifica, arranca", pero quedaba un escalón honesto: `poetry install`. Esta entrada lo colapsa en un comando, no por estética sino porque es un argumento de financiamiento concreto.

---

## [ES]

### 1) Qué cambió y por qué ahora
Los financiadores institucionales (NDI, Carter Center, #StartSmall) evalúan "tiempo hasta desplegar por no-expertos" como una medida de riesgo del grant. La distancia entre "código listo" y "corriendo" era un paso de instalación que un observador local sin Python no domina. `scripts/bootstrap.sh` lo cierra: un comando que instala dependencias, corre `centinel doctor` y termina en un veredicto claro GO / NO-GO. Eso es un artefacto demostrable en una propuesta, no marketing.

### 2) Decisiones de implementación
- **Aditivo, no destructivo:** nunca borra, nunca sobrescribe config, nunca fuerza. Códigos de salida: 0 listo, 1 preflight BLOCKED, 2 fallo de setup.
- **Poetry preferido, pip como respaldo:** si hay Poetry, `install --only main`; si no, venv local desde `requirements-prod.txt`. Funciona en máquina mínima.
- **El preflight es la compuerta:** si `doctor` devuelve BLOCKED, el servidor NO arranca. No se sirve evidencia sobre una postura insegura.
- **Servir es explícito:** por defecto solo instala + verifica. `--serve` levanta la API. Arrancar un proceso largo es una acción mayor; requiere intención explícita.
- **Bilingüe y legible en frío:** salida pensada para alguien que llega sin contexto.

### 3) Impacto
Un observador corre una línea y sabe, antes del día electoral, si el despliegue es seguro. Para la propuesta: prueba que el sistema se despliega sin enviar ingenieros — el escalón que hacía la promesa honesta a medias ahora es de un clic.

### 4) Aprendizaje
La fricción de instalación no es un detalle técnico: es la diferencia entre un grant aprobado y uno rechazado. Cerrar el último escalón valía más que cualquier feature nueva.

---

## [EN]

### 1) What changed and why now
Institutional funders (NDI, Carter Center, #StartSmall) score "time-to-deploy by non-experts" as grant risk. The gap between "code ready" and "running" was an install step a local observer without Python cannot drive. `scripts/bootstrap.sh` closes it: one command installs deps, runs `centinel doctor`, ends in a clear GO / NO-GO verdict — a demoable proposal artifact, not marketing.

### 2) Implementation choices
- **Additive, non-destructive:** never deletes, overwrites config, or forces. Exit codes: 0 ready, 1 preflight BLOCKED, 2 setup failure.
- **Poetry preferred, pip fallback:** `install --only main` if Poetry, else local venv from `requirements-prod.txt`.
- **Preflight is the gate:** on BLOCKED the server does NOT start — no evidence served on an unsafe posture.
- **Serving is explicit:** default is install + verify only; `--serve` launches the API. A long-running process is a bigger action requiring explicit intent.
- **Bilingual, cold-readable** output.

### 3) Impact
An observer runs one line and learns, before election day, whether the deployment is safe. For the proposal: proof the system deploys without sending engineers — the step that made the promise half-honest is now one click.

### 4) Takeaway
Install friction is not a technical detail: it is the difference between a funded and a rejected grant. Closing the last step was worth more than any new feature.

---

## Cierre / Close
Un comando, no destructivo, con compuerta de seguridad y veredicto claro. La promesa a la gente común y a quien la financia ahora es defendible de extremo a extremo.
