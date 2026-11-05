# Origin / Origen

## English

VIGIL began during the 2025 Honduran general election as a practical response to a
simple asymmetry: electoral authorities publish machine-readable results, but the
public historically lacked a zero-cost way to (1) preserve what was published,
(2) detect silent alteration after publication, and (3) flag statistical
irregularities for human review.

Early work consisted of manual downloads of the public CNE JSON endpoints and
comparison across time. That workflow was later automated so that custody and
analysis would not depend on a single operator staying online.

Design constraints that survived into the current architecture:

- **Public data only.** No privileged credentials, no access agreements, no
  scraping of anything the authority has not already published.
- **Bounded request budget.** Scope is deliberately limited to the national
  endpoint plus 18 departmental endpoints, under a hard per-host ceiling of 480
  requests/hour with automatic interval stretching. The system is designed never
  to constitute a load problem for the audited infrastructure. This is an ethical
  constraint accepted at a cost in statistical power — see the aggregate-units
  limitation in `docs/research/FALSE_POSITIVE_ANALYSIS.md`.
- **Minimal personal data.** The system hashes and analyzes electoral aggregates,
  never voter-level records.
- **Offline third-party verification.** `verify/verify_chain.py` uses the Python
  standard library alone, so verification never requires trusting this project's
  dependencies or infrastructure.
- **Hostile network and social environment** assumed around election week.

Authorship is published under the pseudonym **VectisDev** for operator safety.

## Español

VIGIL surgió durante las elecciones generales de Honduras de 2025 como respuesta
práctica a una asimetría simple: las autoridades electorales publican resultados
legibles por máquina, pero el público históricamente carecía de una forma de
coste cero para (1) preservar lo publicado, (2) detectar alteraciones silenciosas
posteriores a la publicación, y (3) señalar irregularidades estadísticas para
revisión humana.

El trabajo inicial consistió en descargas manuales de los endpoints JSON públicos
del CNE y su comparación en el tiempo. Ese flujo se automatizó después para que la
custodia y el análisis no dependieran de que un solo operador permaneciera en
línea.

Restricciones de diseño que sobrevivieron hasta la arquitectura actual:

- **Solo datos públicos.** Sin credenciales privilegiadas ni acuerdos de acceso.
- **Presupuesto de peticiones acotado.** El alcance se limita a propósito al
  endpoint nacional más 18 departamentales, bajo un techo duro de 480
  peticiones/hora por host con estiramiento automático del intervalo. El sistema
  está diseñado para no constituir nunca un problema de carga para la
  infraestructura auditada. Es una restricción ética aceptada a costa de potencia
  estadística.
- **Mínimo dato personal.** Se analizan agregados electorales, nunca registros
  individuales de votantes.
- **Verificación offline por terceros.** `verify/verify_chain.py` usa solo la
  biblioteca estándar.
- **Entorno de red y social hostil** asumido en la semana electoral.

La autoría se publica bajo el seudónimo **VectisDev** por seguridad del operador.
