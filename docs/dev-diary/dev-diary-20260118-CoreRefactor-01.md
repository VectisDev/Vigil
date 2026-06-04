# Dev Diary - 202601 - CoreRefactor - 01

**Fecha aproximada / Approximate date:** 18-ene-2026 / January 18, 2026  
**Fase / Phase:** Refactor estructural y consolidacion / Structural refactor & consolidation  
**Version interna / Internal version:** v0.0.40  
**Rama / Branch:** main (dev-6)  
**Autor / Author:** userf8a2c4

**Resumen de avances / Summary of progress:**
- Integre `dev-v4` completo en `main` con refactor masivo a estructura `src/`.  
  Merged full `dev-v4` into `main` with a major refactor to `src/` layout.
- Madure el Command Center y modularice las reglas de anomalias.  
  Matured the Command Center and modularized anomaly rules.
- Corregi y mejore scraping, generacion de PDFs y flujos principales.  
  Fixed and improved scraping, PDF generation, and core flows.
- Actualice la licencia y prepare el terreno para integracion con frontend.  
  Updated the license and prepared for frontend integration.

---
# Integracion Mayor dev-v4 a main -- Consolidacion y Refactor 2026

/dev: Notas del parche: Version: v0.0.40 (integracion dev-v4)

## [ES] Diario de desarrollo -- C.E.N.T.I.N.E.L.

**Version:** v0.0.40  
**Fecha:** 18-ene-2026  
**Autor:** userf8a2c4

### Contexto y por que lo hice

Llevaba semanas acumulando trabajo en la rama `dev-v4` -- mas de 150 commits entre refactorizacion estructural, el nuevo Command Center, el modulo de analisis modular, y las reglas de anomalias reorganizadas. El codigo habia crecido bastante, y me di cuenta de que seguir trabajando en ramas separadas ya no tenia sentido. Necesitaba consolidar todo en `main` y convertirla en la unica linea activa de desarrollo. Tambien aproveche para adoptar la licencia AGPL-3.0 actualizada que habia preparado el 15 de enero.

### La reorganizacion a `src/`

El cambio mas grande que hice fue migrar todo el codigo a una estructura `src/` estandar. Lo decidi porque la organizacion anterior se estaba volviendo insostenible: las importaciones eran confusas, localizar archivos era lento, y me preocupaba que cuando el equipo creciera o necesitara empaquetar el proyecto, la estructura no aguantaria. Despues de la migracion, el codigo quedo mucho mas organizado y escalable. Fue un trabajo tedioso pero necesario.

### El Command Center

Implemente y madure el Command Center, que es basicamente el punto central desde donde se gestiona todo: scraping, reglas de anomalias, monitoreo en tiempo real. Antes de esto, la operacion diaria era bastante manual -- tenia que invocar scripts individuales, editar configuraciones en varios lugares, y programar tareas a mano. El Command Center centraliza todo eso. Me facilita mucho el dia a dia, y cualquier operador futuro lo va a agradecer.

### Modularizacion de reglas de anomalias

Separe las reglas de anomalias en modulos independientes bajo `command_center/rules/`. Antes estaban creciendo desordenadas dentro de un solo archivo, lo cual hacia dificil probar reglas individuales o desactivar alguna sin tocar el resto. Ahora cada regla es independiente y editable por separado. Esto tambien mejora la transparencia del sistema -- cualquier auditor externo puede ver exactamente que se esta detectando como anomalo y por que.

### Correcciones y mejoras incrementales

Ademas del refactor grande, fui corrigiendo multiples problemas que habia ido encontrando durante semanas de desarrollo intensivo: ajustes en scraping, mejoras en la generacion de PDFs, correcciones en endpoints del CNE, y estabilizacion de flujos principales. Nada de esto era glamoroso, pero era necesario para que el sistema estuviera realmente listo para pruebas de integracion con el frontend que estoy desarrollando en paralelo.

### Cambios tecnicos

- Migracion masiva de codigo a nueva estructura `src/` (refactor estructural profundo)
- Creacion y evolucion de carpeta `command_center/` con settings, rules, scheduler
- Reemplazo de `analyze_rules` por conjunto temporal de reglas + sistema modular
- Modularizacion del modulo de analisis en un paquete con componentes independientes
- Actualizaciones en `pdf_generator.py`, `main.py`, `requirements.txt`, flujos de scraping
- Multiples merges y limpiezas de ramas antiguas (`dev-v3` a `dev-v4`)
- Actualizacion de LICENSE (adoptando AGPL-3.0 actualizada de main, commit 15-ene-2026) y documentacion inicial de refactor

### Lo que pienso mirando hacia adelante

Despues de este merge, decidi que voy a eliminar las ramas antiguas (`dev-v3`, `dev-v2`, etc.) para evitar confusion. Los proximos pasos principales son estabilizar los bugs que encuentre en pruebas de integracion, conectar con el frontend (centinel-app), mejorar la documentacion, y preparar la primera release publica v0.1.0.

Algo que me emociona es que ya estoy viendo como la arquitectura modular -- scrapers configurables, reglas independientes, analisis generico -- abre la posibilidad real de adaptar el sistema a contextos electorales de otros paises en el futuro. Por eso me voy a centrar en un desarrollo que sea lo mas agnostico y globalmente implementable posible, manteniendo siempre el foco inicial en Honduras.

El proyecto sigue siendo privado por ahora, lo cual es perfecto para hacer este tipo de reorganizacion sin impactar a usuarios externos. Siento que este fue un gran avance -- estoy pasando de un prototipo desordenado a un sistema mucho mas profesional y mantenible.

Este proyecto nace de mi deseo de contribuir, como ciudadano, al fortalecimiento de la democracia en mi pais. Desde la tecnologia busco ofrecer herramientas abiertas, objetivas y transparentes que permitan que los datos electorales hablen por si mismos, sin intermediarios ni interpretaciones. Solo hechos, al servicio de todas las personas que quieran verificarlos.

**Objetivo de C.E.N.T.I.N.E.L.:** Monitoreo independiente, neutral y transparente de datos electorales publicos. Solo numeros. Solo hechos. Codigo abierto (AGPL-3.0) para el pueblo hondureno.

---

## [EN] Development journal -- C.E.N.T.I.N.E.L.

**Version:** v0.0.40  
**Date:** January 18, 2026  
**Author:** userf8a2c4

### Context and why I did it

I had been accumulating work on the `dev-v4` branch for weeks -- over 150 commits of structural refactoring, the new Command Center, the modular analysis module, and reorganized anomaly rules. The code had grown substantially, and I realized that continuing to work on separate branches no longer made sense. I needed to consolidate everything into `main` and make it the sole active development line. I also took the opportunity to adopt the updated AGPL-3.0 license I had prepared on January 15.

### The `src/` reorganization

The biggest change I made was migrating all the code to a standard `src/` layout. I decided on this because the previous organization was becoming unsustainable: imports were confusing, finding files was slow, and I worried that when the team grew or I needed to package the project, the structure wouldn't hold up. After the migration, the code was much more organized and scalable. It was tedious work but necessary.

### The Command Center

I implemented and matured the Command Center, which is basically the central point from which everything is managed: scraping, anomaly rules, real-time monitoring. Before this, daily operations were quite manual -- I had to invoke individual scripts, edit configurations in multiple places, and schedule tasks by hand. The Command Center centralizes all of that. It makes my day-to-day much easier, and any future operator will appreciate it.

### Anomaly rules modularization

I separated the anomaly rules into independent modules under `command_center/rules/`. Before, they were growing messily inside a single file, which made it hard to test individual rules or disable one without touching the rest. Now each rule is independent and editable on its own. This also improves the system's transparency -- any external auditor can see exactly what is being detected as anomalous and why.

### Incremental fixes and improvements

Beyond the big refactor, I kept fixing multiple issues I had been finding during weeks of intensive development: scraping adjustments, PDF generation improvements, CNE endpoint fixes, and core flow stabilization. None of this was glamorous, but it was necessary to get the system truly ready for integration testing with the frontend I'm developing in parallel.

### Technical Changes

- Massive code migration to new `src/` layout (deep structural refactor)
- Creation/evolution of `command_center/` folder (settings, rules, scheduler)
- Replacement of `analyze_rules` with modular temporary rule set
- Modular analysis package split into dedicated independent components
- Updates to `pdf_generator.py`, `main.py`, `requirements.txt`, scraping flows
- Multiple branch merges and old branch cleanups
- LICENSE update (adopting current AGPL-3.0 from main, Jan 15 2026 commit) and initial refactor documentation updates

### Looking ahead

After this merge, I decided to delete the old branches (`dev-v3`, `dev-v2`, etc.) to avoid confusion. The main next steps are stabilizing bugs found in integration tests, connecting with the frontend (centinel-app), improving documentation, and preparing the first public release v0.1.0.

Something that excites me is that I'm already seeing how the modular architecture -- configurable scrapers, independent rules, generic analysis -- opens real possibilities for adapting the system to electoral contexts in other countries in the future. That's why I'm going to focus on development that is as agnostic and globally implementable as possible, while keeping the initial focus on Honduras.

The project is still private for now, which is perfect for doing this kind of reorganization without impacting external users. I feel this was a major step forward -- I'm moving from a messy prototype to a much more professional and maintainable system.

This project is born from my desire to contribute, as a citizen, to strengthening democracy in my country. Through technology I aim to provide open, objective, and transparent tools that allow electoral data to speak for itself, without intermediaries or interpretations. Just facts, at the service of everyone who wants to verify them.

**C.E.N.T.I.N.E.L. Goal:** Independent, neutral and transparent monitoring of public electoral data. Only numbers. Only facts. Open-source (AGPL-3.0) for the Honduran people.
