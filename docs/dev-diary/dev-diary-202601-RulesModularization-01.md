# Dev Diary - 202601 - RulesModularization - 01

**Fecha aproximada / Approximate date:** 11-ene-2026 / January 11, 2026  
**Fase / Phase:** Modularizacion de reglas y reglas forenses / Rule modularization & forensic rules  
**Version interna / Internal version:** v0.0.31  
**Rama / Branch:** main (dev-6)  
**Autor / Author:** userf8a2c4

**Resumen de avances / Summary of progress:**
- Modularice completamente las reglas de analisis en `centinel/core/rules/`.  
  Fully modularized analysis rules under `centinel/core/rules/`.
- Agregue nuevas reglas forenses (trend shift, processing speed, irreversibility).  
  Added new forensic rules (trend shift, processing speed, irreversibility).
- Cree un orquestador configurable en `scripts/analyze_rules.py` con reglas habilitables por config.  
  Built a configurable orchestrator in `scripts/analyze_rules.py` with config-driven rule toggles.
- Escribi pruebas de orquestacion y ajuste la configuracion en `config.yaml`.  
  Wrote orchestrator tests and updated configuration in `config.yaml`.

---
# [ES] Refactor modular de reglas + nuevas reglas forenses

  /dev: Notas del parche: Version: v0.0.31 (commit ae6296f)

## [ES] Diario de desarrollo -- C.E.N.T.I.N.E.L.

**Version:** v0.0.31  
**Fecha:** 11-ene-2026  
**Autor:** userf8a2c4

### El problema que vi

Las reglas de analisis se me habian ido acumulando en un solo archivo grande, y estaba llegando al punto en que mantenerlo era insostenible. Cada vez que queria probar una regla individual, tenia que cargar todo el modulo. Si queria desactivar una regla temporalmente, tenia que comentar codigo. Y lo peor: si algo fallaba en una regla, el error se propagaba y afectaba a las demas. Me di cuenta de que necesitaba separar cada regla en su propio modulo y crear un orquestador que las ejecutara de forma independiente.

Ademas, tenia en mente tres tipos de deteccion forense que queria implementar desde hacia tiempo: cambios abruptos de tendencia, velocidades de procesamiento no humanas, y resultados estadisticamente irreversibles. Decidi que el refactor modular era el momento perfecto para agregarlas.

### Lo que hice

Cree el paquete `centinel/core/rules/` y movi cada regla a su propio archivo: Benford, ML outliers, diffs basicos, participacion, trend shift, processing speed, e irreversibility. Cada regla tiene helpers compartidos, docstrings bilingues, y manejo robusto de errores para datos nulos o timestamps invalidos.

Escribi las tres nuevas reglas forenses:
- **Trend shift** detecta desviaciones abruptas en la tendencia de resultados entre snapshots consecutivos.
- **Processing speed** identifica velocidades de procesamiento de actas que serian imposibles para operadores humanos.
- **Irreversibility** marca cuando un resultado se vuelve estadisticamente irreversible antes de lo esperado.

Estas tres me parecian criticas para la fase de TREP, donde la deteccion en tiempo real importa mas que nunca.

Despues construi el orquestador en `scripts/analyze_rules.py`. Lo disene para que use una lista `RULES` y la funcion `run_all_rules`, ejecutando unicamente las reglas habilitadas en `config.yaml`. Esto me da flexibilidad operativa -- puedo activar o desactivar reglas sin tocar codigo, solo editando la configuracion.

Finalmente, escribi pruebas del orquestador en `tests/test_rules_orchestrator.py` y actualice los parametros de configuracion bajo `rules` en `config.yaml` y `config.example.yaml`.

### Cambios tecnicos

- Cree el paquete `centinel/core/rules/` con helpers y reglas individuales (Benford, ML outliers, diffs basicos, participacion, trend shift, processing speed, irreversibility)
- `scripts/analyze_rules.py` ahora usa `run_all_rules` y una lista `RULES` para ejecutar unicamente las reglas habilitadas
- Agregue parametros de configuracion bajo `rules` en `config.yaml` y `config.example.yaml`
- Inclui pruebas del orquestador en `tests/test_rules_orchestrator.py`

### Lo que aprendi

Separar las reglas fue de esas decisiones que parecen "solo reorganizacion" pero que cambian completamente la experiencia de desarrollo. Ahora puedo iterar sobre una regla sin miedo a romper las demas, y las alertas que se consolidan en `analysis_results.json` y `anomalies_report.json` son mucho mas trazables porque se exactamente que regla las genero.

**Objetivo de C.E.N.T.I.N.E.L.:** Monitoreo independiente, neutral y transparente de datos electorales publicos. Solo numeros. Solo hechos. Codigo abierto MIT para el pueblo hondureno.


-------------


# [EN] Modular rules refactor + new forensic rules

## [EN] Development journal -- C.E.N.T.I.N.E.L.

**Version:** v0.0.31  
**Date:** January 11, 2026  
**Author:** userf8a2c4

### The problem I saw

The analysis rules had been piling up in a single large file, and I was reaching the point where maintaining it was unsustainable. Every time I wanted to test an individual rule, I had to load the entire module. If I wanted to temporarily disable a rule, I had to comment out code. And worst of all: if something failed in one rule, the error would propagate and affect the others. I realized I needed to separate each rule into its own module and create an orchestrator to run them independently.

On top of that, I had been wanting to implement three types of forensic detection for a while: abrupt trend shifts, non-human processing speeds, and statistically irreversible outcomes. I decided the modular refactor was the perfect time to add them.

### What I did

I created the `centinel/core/rules/` package and moved each rule into its own file: Benford, ML outliers, basic diffs, participation, trend shift, processing speed, and irreversibility. Each rule has shared helpers, bilingual docstrings, and robust error handling for null data or invalid timestamps.

I wrote the three new forensic rules:
- **Trend shift** detects abrupt deviations in result trends between consecutive snapshots.
- **Processing speed** identifies ballot processing speeds that would be impossible for human operators.
- **Irreversibility** flags when a result becomes statistically irreversible earlier than expected.

These three felt critical for the TREP phase, where real-time detection matters more than ever.

Then I built the orchestrator in `scripts/analyze_rules.py`. I designed it to use a `RULES` list and the `run_all_rules` function, executing only the rules enabled in `config.yaml`. This gives me operational flexibility -- I can toggle rules on or off without touching code, just by editing the configuration.

Finally, I wrote orchestrator tests in `tests/test_rules_orchestrator.py` and updated the configuration parameters under `rules` in `config.yaml` and `config.example.yaml`.

### Technical Changes

- Created `centinel/core/rules/` package with helpers and individual rules (Benford, ML outliers, basic diffs, participation, trend shift, processing speed, irreversibility)
- `scripts/analyze_rules.py` now uses `run_all_rules` and a `RULES` list to run only enabled rules
- Added rule configuration under `rules` in `config.yaml` and `config.example.yaml`
- Included orchestrator tests in `tests/test_rules_orchestrator.py`

### What I learned

Separating the rules was one of those decisions that seems like "just reorganization" but completely changes the development experience. Now I can iterate on a rule without fear of breaking the others, and the alerts consolidated in `analysis_results.json` and `anomalies_report.json` are much more traceable because I know exactly which rule generated them.

**C.E.N.T.I.N.E.L. Goal:** Independent, neutral and transparent monitoring of public electoral data. Only numbers. Only facts. MIT open-source for the Honduran people.
