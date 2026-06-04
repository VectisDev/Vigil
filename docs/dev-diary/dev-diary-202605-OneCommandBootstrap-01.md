# Dev Diary - 202605 - OneCommandBootstrap - 01

**Fecha aproximada / Approximate date:** 15-may-2026 / May 15, 2026  
**Fase / Phase:** Colapsar el ultimo escalon de friccion / Collapsing the last friction step  
**Version interna / Internal version:** v0.1.x (ciclo dev-v9)  
**Rama / Branch:** dev-v9  
**Autor / Author:** userf8a2c4

**Contexto / Context:**  
Continuacion de `dev-diary-202605-MediumGapsHardening-01.md`. TIER 5 dejo "pon el modo, verifica, arranca", pero quedaba un escalon honesto: `poetry install`. Esta entrada lo colapsa en un comando, no por estetica sino porque es un argumento de financiamiento concreto.

---

## [ES]

### 1) Que cambio y por que ahora
Los financiadores institucionales (NDI, Carter Center, #StartSmall) evaluan "tiempo hasta desplegar por no-expertos" como una medida de riesgo del grant. La distancia entre "codigo listo" y "corriendo" era un paso de instalacion que un observador local sin Python no domina. Decidi crear `scripts/bootstrap.sh` para cerrarlo: un comando que instala dependencias, corre `centinel doctor` y termina en un veredicto claro GO / NO-GO. Eso es un artefacto demostrable en una propuesta, no marketing.

### 2) Decisiones de implementacion
- **Aditivo, no destructivo:** nunca borra, nunca sobrescribe config, nunca fuerza. Codigos de salida: 0 listo, 1 preflight BLOCKED, 2 fallo de setup.
- **Poetry preferido, pip como respaldo:** si hay Poetry, `install --only main`; si no, venv local desde `requirements-prod.txt`. Funciona en maquina minima.
- **El preflight es la compuerta:** si `doctor` devuelve BLOCKED, el servidor NO arranca. No se sirve evidencia sobre una postura insegura.
- **Servir es explicito:** por defecto solo instala + verifica. `--serve` levanta la API. Arrancar un proceso largo es una accion mayor; requiere intencion explicita.
- **Bilingue y legible en frio:** salida pensada para alguien que llega sin contexto.

### 3) Impacto
Un observador corre una linea y sabe, antes del dia electoral, si el despliegue es seguro. Para la propuesta: prueba que el sistema se despliega sin enviar ingenieros -- el escalon que hacia la promesa honesta a medias ahora es de un clic.

### 4) Aprendizaje
La friccion de instalacion no es un detalle tecnico: es la diferencia entre un grant aprobado y uno rechazado. Cerrar el ultimo escalon valio mas que cualquier feature nueva.

---

## [EN]

### 1) What changed and why now
Institutional funders (NDI, Carter Center, #StartSmall) score "time-to-deploy by non-experts" as grant risk. The gap between "code ready" and "running" was an install step a local observer without Python cannot drive. I decided to create `scripts/bootstrap.sh` to close it: one command installs deps, runs `centinel doctor`, ends in a clear GO / NO-GO verdict -- a demoable proposal artifact, not marketing.

### 2) Implementation choices
- **Additive, non-destructive:** never deletes, overwrites config, or forces. Exit codes: 0 ready, 1 preflight BLOCKED, 2 setup failure.
- **Poetry preferred, pip fallback:** `install --only main` if Poetry, else local venv from `requirements-prod.txt`.
- **Preflight is the gate:** on BLOCKED the server does NOT start -- no evidence served on an unsafe posture.
- **Serving is explicit:** default is install + verify only; `--serve` launches the API. A long-running process is a bigger action requiring explicit intent.
- **Bilingual, cold-readable** output.

### 3) Impact
An observer runs one line and learns, before election day, whether the deployment is safe. For the proposal: proof the system deploys without sending engineers -- the step that made the promise half-honest is now one click.

### 4) Takeaway
Install friction is not a technical detail: it is the difference between a funded and a rejected grant. Closing the last step was worth more than any new feature.

---

## Cierre / Close
Un comando, no destructivo, con compuerta de seguridad y veredicto claro. La promesa a la gente comun y a quien la financia ahora es defendible de extremo a extremo.
