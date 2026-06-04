# Dev Diary - 202601 - BootstrapDocs - 01

**Fecha aproximada / Approximate date:** 22-ene-2026 / January 22, 2026  
**Fase / Phase:** Inicio simplificado y documentacion / Simplified bootstrap & documentation  
**Version interna / Internal version:** v0.0.41 (dev-v5)  
**Rama / Branch:** dev-v5  
**Autor / Author:** userf8a2c4

**Resumen de avances / Summary of progress:**
- Cree un helper de bootstrap y un Makefile para estandarizar el arranque.  
  Built a bootstrap helper and Makefile to standardize startup.
- Actualice README, QUICKSTART y la documentacion de scripts.  
  Updated README, QUICKSTART, and scripts documentation.
- Ajuste el manual operativo con notas de despliegue.  
  Updated the operational manual with deployment notes.

---
# [ES] Inicio simplificado dev-v5 -- Bootstrap y documentacion 2026

  /dev: Notas del parche: Version: v0.0.41_-_dev-v5 (commit c5f6585)

**Version:** v0.0.41_-_dev-v5  
**Fecha:** 22-ene-2026  
**Autor:** userf8a2c4

### Por que hice esto

Despues del refactor grande a `src/` y la integracion de dev-v4, me di cuenta de que arrancar el proyecto desde cero se habia vuelto confuso. Habia demasiados pasos manuales, dependencias que no estaban documentadas, y cada vez que intentaba levantar el entorno en limpio me encontraba con algun paso que habia olvidado. Si yo mismo tenia problemas, cualquier otro colaborador lo tendria peor. Decidi que era momento de invertir en la experiencia de onboarding.

### Lo que hice

Escribi un script de bootstrap (`scripts/bootstrap.py`) que prepara todas las dependencias y la configuracion base automaticamente. Tambien cree un `Makefile` con los comandos mas comunes para que nadie tenga que recordar las invocaciones exactas. La idea es que con un solo comando puedas tener el entorno listo.

Actualice el README, el QUICKSTART y la documentacion de scripts para que reflejaran el flujo real de arranque. Antes habia discrepancias entre lo que decia la documentacion y lo que realmente funcionaba, y eso me frustraba. Tambien ajuste el manual operativo con notas de despliegue que habia ido acumulando durante las semanas anteriores.

Aproveche para actualizar la documentacion de licencia y asegurarme de que reflejara correctamente la AGPL-3.0.

### Cambios tecnicos

- Nuevos comandos de automatizacion en `Makefile`
- Script de bootstrap para preparar dependencias y configuracion base
- Ajustes en `README.md`, `QUICKSTART.md`, `docs/manual.md` y `scripts/README.md`

### Lo que aprendi

A veces la documentacion y las herramientas de arranque no se sienten como "progreso real" porque no agregan funcionalidad. Pero me di cuenta de que sin ellas, todo lo demas se vuelve mas lento. Recomiendo ejecutar el flujo de bootstrap antes del primer arranque para evitar configuraciones incompletas.

**Objetivo de C.E.N.T.I.N.E.L.:** Monitoreo independiente, neutral y transparente de datos electorales publicos. Solo numeros. Solo hechos. Codigo abierto AGPL-3.0 para el pueblo hondureno.


-------------


# [EN] Simplified bootstrap dev-v5 -- Bootstrap and documentation 2026

**Version:** v0.0.41_-_dev-v5  
**Date:** January 22, 2026  
**Author:** userf8a2c4

### Why I did this

After the big refactor to `src/` and the dev-v4 integration, I realized that setting up the project from scratch had become confusing. There were too many manual steps, undocumented dependencies, and every time I tried to spin up a clean environment I'd run into some step I had forgotten. If I was having trouble myself, any other collaborator would have it worse. I decided it was time to invest in the onboarding experience.

### What I did

I wrote a bootstrap script (`scripts/bootstrap.py`) that prepares all dependencies and base configuration automatically. I also created a `Makefile` with the most common commands so nobody has to remember the exact invocations. The idea is that with a single command you can have the environment ready.

I updated the README, QUICKSTART, and scripts documentation so they reflected the actual startup flow. Before, there were discrepancies between what the docs said and what actually worked, and that frustrated me. I also updated the operational manual with deployment notes I had been accumulating over the previous weeks.

I took the opportunity to update the license documentation and make sure it correctly reflected AGPL-3.0.

### Technical Changes

- New automation commands in `Makefile`
- Bootstrap script to prepare dependencies and base configuration
- Updates to `README.md`, `QUICKSTART.md`, `docs/manual.md`, and `scripts/README.md`

### What I learned

Sometimes documentation and bootstrap tooling don't feel like "real progress" because they don't add functionality. But I realized that without them, everything else becomes slower. I recommend running the bootstrap flow before first startup to avoid incomplete setup.

**C.E.N.T.I.N.E.L. Goal:** Independent, neutral and transparent monitoring of public electoral data. Only numbers. Only facts. AGPL-3.0 open-source for the Honduran people.
