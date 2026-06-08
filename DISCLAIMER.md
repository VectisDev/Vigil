# CENTINEL — Declaración de Neutralidad y Limitaciones
# CENTINEL — Neutrality Statement and Limitations

**Versión / Version:** 1.0 · **Fecha / Date:** 2026-06-07
**Licencia / License:** AGPL-3.0 · **Repositorio / Repository:** github.com/VectisDev/centinel

---

## Español

### Qué es CENTINEL

CENTINEL es un sistema de software libre que captura, encadena criptográficamente
y analiza estadísticamente los datos que publican las autoridades electorales de
manera pública durante procesos electorales. CENTINEL analiza exclusivamente
**datos públicos** publicados por organismos electorales en formato digital.
CENTINEL **no analiza actas físicas** ni tiene acceso a sistemas internos de
ninguna autoridad electoral.

### Lo que CENTINEL hace

- Captura datos electorales públicos disponibles en línea.
- Los encadena criptográficamente para detectar modificaciones posteriores
  a su publicación (SHA-256 chained hash).
- Aplica pruebas estadísticas y forenses para identificar patrones anómalos.
- Genera reportes técnicos con evidencia verificable por cualquier tercero.

### Lo que CENTINEL NO hace

- **CENTINEL no afirma fraude electoral** en ninguna circunstancia.
- **CENTINEL no emite juicios políticos** ni favorece a ningún partido,
  candidato, organización o gobierno.
- **CENTINEL no accede** a sistemas, redes o datos que no sean públicos.
- **CENTINEL no reemplaza** la observación electoral institucional.
- **CENTINEL no es evidencia jurídica** por sí mismo — es evidencia técnica
  para ser evaluada por expertos, observadores y autoridades competentes.

### Interpretación de resultados

Las anomalías estadísticas detectadas por CENTINEL son **señales cuantitativas**
que indican desviaciones de patrones esperados en los datos disponibles.
La interpretación de su significado — incluyendo si representan irregularidades,
errores técnicos, cambios metodológicos u otros fenómenos — corresponde
exclusivamente a evaluadores humanos independientes con acceso al contexto
completo del proceso electoral.

### Reproducibilidad

Todos los análisis de CENTINEL son completamente reproducibles. Cualquier persona
puede verificar los resultados ejecutando el mismo software sobre los mismos datos
públicos. Los datos capturados se publican automáticamente con su cadena de hashes
verificable offline mediante `verify/verify_chain.py`, sin dependencias externas.

### Limitaciones técnicas

Los resultados de CENTINEL están sujetos a las limitaciones de los datos fuente:
si la autoridad electoral publica datos incompletos, con retrasos, o en formatos
no estructurados, la calidad del análisis se reduce proporcionalmente. CENTINEL
reporta explícitamente cuando los datos son insuficientes para una prueba.

---

## English

### What CENTINEL is

CENTINEL is free software that captures, cryptographically chains, and statistically
analyzes data published publicly by electoral authorities during elections.
CENTINEL analyzes exclusively **public data** published by electoral bodies in
digital format. CENTINEL does **not analyze physical ballot documents** nor does
it have access to any electoral authority's internal systems.

### What CENTINEL does

- Captures publicly available electoral data.
- Cryptographically chains it to detect post-publication modifications (SHA-256).
- Applies statistical and forensic tests to identify anomalous patterns.
- Generates technical reports with evidence verifiable by any third party.

### What CENTINEL does NOT do

- **CENTINEL does not allege electoral fraud** under any circumstances.
- **CENTINEL does not make political judgments** nor does it favor any party,
  candidate, organization, or government.
- **CENTINEL does not access** systems, networks, or data that are not public.
- **CENTINEL does not replace** institutional electoral observation.
- **CENTINEL is not legal evidence** on its own — it is technical evidence
  for evaluation by experts, observers, and competent authorities.

### Interpretation of results

Statistical anomalies detected by CENTINEL are **quantitative signals** indicating
deviations from expected patterns in the available data. The interpretation of
their significance — including whether they represent irregularities, technical
errors, methodological changes, or other phenomena — rests exclusively with
independent human evaluators with full access to the electoral process context.

### Reproducibility

All CENTINEL analyses are fully reproducible. Anyone can verify results by running
the same software on the same public data. Captured data is published automatically
with a verifiable hash chain, checkable offline using `verify/verify_chain.py`
with no external dependencies.

### Technical limitations

CENTINEL results are subject to source data limitations: if the electoral authority
publishes incomplete, delayed, or unstructured data, analysis quality is
proportionally reduced. CENTINEL explicitly reports when data is insufficient
for a given test.

---

*CENTINEL — Software libre de auditoría electoral · Free electoral audit software*
*AGPL-3.0 · Políticamente neutral / Politically neutral · github.com/VectisDev/centinel*
