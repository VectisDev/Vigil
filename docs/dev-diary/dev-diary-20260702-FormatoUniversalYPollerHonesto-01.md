# 20260702 — Formato universal y poller honesto

**Fecha:** 2 de julio de 2026

Hoy cerré dos deudas que venía arrastrando desde que empecé a pensar en VIGIL
más allá de Honduras.

## La pregunta incómoda: ¿de verdad podemos con 100 endpoints cada 3 minutos?

Me senté a auditar los jobs asíncronos porque el número "100 endpoints" me
daba vueltas. La respuesta corta: el motor sí puede — asyncio despacha 100
fetches en paralelo en segundos — pero el número solo existía en comentarios
del código. En producción tenemos 19 endpoints, todos del mismo host del CNE,
y el poller de 3 minutos corría sin retry, sin manejo de 429 y con un push a
git por cada ciclo. Toda la lógica de cortesía (backoff, circuit breaker,
robots.txt) vivía en el otro colector, el de cron.

Y había una contradicción matemática que nadie había puesto sobre la mesa:
nuestro propio techo ético es 480 requests/hora por host. Con 100 endpoints
de un mismo organismo a ciclo de 3 minutos serían 2,000 req/h — cuatro veces
el límite que nosotros mismos nos impusimos. No iba a mover el techo: el
límite ético de una consulta cada 3 minutos es el estándar que defendimos
desde el día uno (NYT/MinnPost), y proteger el servidor del ente electoral
no es negociable.

La solución fue hacer el compromiso honesto y aplicarlo en código:

- El cap de **100 endpoints ahora se aplica de verdad** (`MAX_ENDPOINTS`,
  truncado con warning). Cien es deliberado: el doble de los 50 estados de
  EE.UU., suficiente para cualquier país del continente.
- El **piso de 3 minutos** también (`ETHICAL_FLOOR_SECONDS`), con el mismo
  desbloqueo de emergencia que ya existía en el panel para el preset de
  apagón.
- Lo nuevo importante: `resolve_safe_interval()` calcula el presupuesto por
  host. Con ≤24 endpoints por host los 3 minutos se sostienen (Honduras con
  sus 19 pasa holgado); con más, el intervalo se estira solo lo necesario y
  lo deja registrado en el log y en `latest_cycle.json`. Cien endpoints
  repartidos entre cinco autoridades: 3 minutos. Cien del mismo host: 12.5
  minutos. Sin trampas.
- El fetch ahora reintenta con backoff y respeta `Retry-After` en 429/5xx,
  y el push a la rama `data` va por lotes (cada 5 ciclos, con pull-rebase y
  reintento) para que los slots solapados del workflow dejen de pisarse.

## Un solo VIGIL para todo el continente

La segunda pieza es la que más ilusión me hace. Cada organismo electoral
publica en su propio formato: Honduras y Guatemala en JSON (TREP), Brasil en
JSON y CSV según el portal, México en CSV por casilla (PREP), Argentina en
CSV/JSON de datos abiertos. Hasta hoy, VIGIL solo hablaba JSON con la forma
exacta del CNE hondureño.

Ahora hay un detector de formato (`format_detector.py`, puro stdlib) que
identifica JSON, CSV, XML, HTML y PDF por contenido — magic bytes, parse
tentativo, `csv.Sniffer` — con el Content-Type y la extensión de URL solo
como desempate. Y un registry de parsers en `schema_adapter.py`: JSON y CSV
convergen en el mismo `Snapshot` canónico que ya consume el motor de reglas.
El de CSV agrega filas por mesa/casilla, detecta el delimitador (el `;` de
México, el latin-1 de Brasil) y auto-mapea columnas con los nombres reales
que usan los organismos del continente: `PARTIDO`, `SG_PARTIDO`,
`agrupacion`, `QT_VOTOS`, `sufragios`… Si no reconoce las columnas, falla
con un error explícito pidiendo el `field_map` — jamás inventa datos.

El resultado es el principio que quería desde el inicio: **cero código por
país**. Elegir país, pegar la URL de resultados, y el sistema detecta el
formato y se adapta. XML y HTML quedan detectados con la puerta abierta
(registrar el parser y listo); PDF es honesto: requiere OCR y eso es otra
fase.

Lo que no se tocó: el camino JSON de Honduras queda byte a byte idéntico —
lo verifiqué con un test de regresión que compara el adaptador dedicado
contra el genérico sobre los fixtures reales de diciembre 2025. La cadena de
hashes no se entera de nada de esto.

También reconcilié la documentación que se contradecía: la cadencia electoral
es 3 minutos (no "5–15") y la tabla de capacidad por host quedó en
RATE_LIMITING.md para que cualquier observador pueda verificar la aritmética.
