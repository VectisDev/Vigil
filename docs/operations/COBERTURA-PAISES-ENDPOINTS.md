# Cobertura por país — endpoints, formato y cadencia real

> Referencia rápida de lo que VIGIL puede solicitar hoy, por país.
> Los números de intervalo son **los que el poller impone automáticamente**
> (`resolve_safe_interval` en `src/centinel/core/poller_async.py`), no aspiraciones.

## Cómo leer esta tabla

- **Divisiones** = unidades administrativas del país (departamentos / estados / provincias /
  regiones). **Endpoints** = 1 nacional + esas divisiones. Es lo que se consulta por ciclo.
- **Formato**: `json` fijado por preset (validado); `auto` = se detecta por contenido
  (JSON o CSV) en la primera captura, sin escribir código.
- **Intervalo mín. (1 host)** = el piso que el sistema aplica solo si **todos** los endpoints
  del país están en un mismo servidor, calculado como `max(180 s, ⌈endpoints × 3600 / 480⌉)`.
  El **piso ético es 3 min**; se estira solo cuando un host superaría el techo de
  **480 requests/hora/host**. Si los endpoints están repartidos en varios hosts (≤24 por host),
  el intervalo vuelve a 3 min.
- **req/h**: carga real contra el servidor a ese intervalo. Siempre ≤ 480.
- **Nivel**: **1** = validado en producción · **2** = listo, el operador provee la URL y el
  formato se detecta al capturar · **2\*** = cubrible pero sin feed nacional único (ver notas) ·
  **3** = preset existe pero no hay portal público de resultados.

---

## Lista completa — los 21 países que se pueden seleccionar

| # | País | Código | Divisiones | Formato | Endpoints | Intervalo mín. (1 host) | req/h | Nivel | Autoridad electoral |
|----|------|--------|-----------|---------|-----------|-------------------------|-------|-------|---------------------|
| 1 | 🇦🇷 Argentina | `AR` | 24 provincias | `auto` | 25 | 3m8s | 479 | 2 | Cámara Nacional Electoral (CNE) |
| 2 | 🇧🇴 Bolivia | `BO` | 9 departamentos | `auto` | 10 | 3m | 200 | 2 | Tribunal Supremo Electoral (TSE) |
| 3 | 🇧🇷 Brasil | `BR` | 27 estados | `auto` | 28 | 3m30s | 480 | 2 | Tribunal Superior Eleitoral (TSE) |
| 4 | 🇨🇱 Chile | `CL` | 16 regiones | `auto` | 17 | 3m | 340 | 2 | Servicio Electoral (SERVEL) |
| 5 | 🇨🇴 Colombia | `CO` | 33 departamentos | `auto` | 34 | 4m15s | 480 | 2 | Registraduría Nacional del Estado Civil |
| 6 | 🇨🇷 Costa Rica | `CR` | 7 provincias | `auto` | 8 | 3m | 160 | 2 | Tribunal Supremo de Elecciones (TSE) |
| 7 | 🇨🇺 Cuba | `CU` | 16 provincias | `auto` | 17 | 3m | 340 | 3 | Consejo Electoral Nacional |
| 8 | 🇪🇨 Ecuador | `EC` | 24 provincias | `auto` | 25 | 3m8s | 479 | 2 | Consejo Nacional Electoral (CNE) |
| 9 | 🇸🇻 El Salvador | `SV` | 14 departamentos | `auto` | 15 | 3m | 300 | 2 | Tribunal Supremo Electoral (TSE) |
| 10 | 🇺🇸 Estados Unidos | `US` | 50 estados | `auto` | 51 | 6m23s | 479 | 2\* | Descentralizado — Secretarios de Estado |
| 11 | 🇬🇹 Guatemala | `GT` | 22 departamentos | `auto` | 23 | 3m | 460 | 2 | Tribunal Supremo Electoral (TSE) |
| 12 | 🇭🇹 Haití | `HT` | 10 departamentos | `auto` | 11 | 3m | 220 | 3 | Conseil Électoral Provisoire (CEP) |
| 13 | 🇭🇳 Honduras | `HN` | 18 departamentos | `json` | 19 | 3m | 380 | 1 | Consejo Nacional Electoral (CNE) |
| 14 | 🇲🇽 México | `MX` | 32 estados | `auto` | 33 | 4m8s | 479 | 2 | Instituto Nacional Electoral (INE / PREP) |
| 15 | 🇳🇮 Nicaragua | `NI` | 17 departamentos | `auto` | 18 | 3m | 360 | 2 | Consejo Supremo Electoral (CSE) |
| 16 | 🇵🇦 Panamá | `PA` | 13 provincias | `auto` | 14 | 3m | 280 | 2 | Tribunal Electoral (TE) |
| 17 | 🇵🇾 Paraguay | `PY` | 18 departamentos | `auto` | 19 | 3m | 380 | 2 | Tribunal Superior de Justicia Electoral (TSJE) |
| 18 | 🇵🇪 Perú | `PE` | 25 regiones | `auto` | 26 | 3m15s | 480 | 2 | Jurado Nacional de Elecciones (JNE) / ONPE |
| 19 | 🇩🇴 Rep. Dominicana | `DO` | 32 provincias | `auto` | 33 | 4m8s | 479 | 2 | Junta Central Electoral (JCE) |
| 20 | 🇺🇾 Uruguay | `UY` | 19 departamentos | `auto` | 20 | 3m | 400 | 2 | Corte Electoral |
| 21 | 🇻🇪 Venezuela | `VE` | 24 estados | `auto` | 25 | 3m8s | 479 | 2 | Consejo Nacional Electoral (CNE) |

**Totales:** 21 países · 471 endpoints en toda la región · 1 validado en producción (Nivel 1) ·
18 listos para campo (Nivel 2) · 1 cubrible sin feed único (Nivel 2\*, EE.UU.) · 2 sin fuente
pública (Nivel 3). Ningún país solo satura un host: todos ≤ 480 req/h al intervalo mostrado.

---

## Fuente real y formato observado por país

Detalle específico de dónde y cómo publica cada autoridad. `auto` significa que VIGIL
detecta el formato al capturar; los marcados **confirmado** provienen de portales de datos
abiertos verificados.

| País | Portal / fuente real | Formato observado | Estado |
|------|----------------------|-------------------|--------|
| 🇭🇳 Honduras | `resultadosgenerales2025.cne.hn` (TREP) | JSON | ✅ Confirmado, validado en prod. 2025 |
| 🇧🇷 Brasil | `dadosabertos.tse.jus.br` (divulgação) | JSON + CSV | ✅ Confirmado (datos abiertos) |
| 🇲🇽 México | `prep.ine.mx` (PREP por casilla) | CSV | ✅ Confirmado (datos abiertos) |
| 🇦🇷 Argentina | `resultados.gob.ar` / `datos.gob.ar` | JSON + CSV | ✅ Confirmado (datos abiertos) |
| 🇬🇹 Guatemala | `resultados.tse.org.gt` | JSON | 🔷 Portal existe; confirmar por elección |
| 🇨🇴 Colombia | `resultados.registraduria.gov.co` | HTML + JSON parcial | 🔷 Mixto; puede requerir parser HTML |
| 🇨🇱 Chile | `servel.cl` | por confirmar | 🔷 Portal existe; `auto` al capturar |
| 🇪🇨 Ecuador · 🇵🇪 Perú · 🇻🇪 Venezuela · 🇧🇴 Bolivia · 🇺🇾 Uruguay · 🇵🇾 Paraguay · 🇸🇻 El Salvador · 🇳🇮 Nicaragua · 🇨🇷 Costa Rica · 🇵🇦 Panamá · 🇩🇴 Rep. Dom. | Portal oficial de la autoridad | por confirmar | 🔷 `auto`; el operador provee la URL |
| 🇺🇸 Estados Unidos | Secretarios de Estado (50, por separado) | JSON/CSV/HTML según estado | ⚠️ Sin feed nacional único (ver abajo) |
| 🇨🇺 Cuba · 🇭🇹 Haití | — | — | ❌ Sin portal público de resultados |

---

## Detalle por nivel de validación

### Nivel 1 — Validado en producción

**Honduras (`HN`)** corrió en la elección general de 2025 con endpoints reales; dataset
anclado a Bitcoin (OpenTimestamps). 19 endpoints en un host → los 3 minutos se sostienen
holgados. Formato JSON (TREP del CNE).

### Nivel 2 — Listos; el operador provee la URL, el formato se detecta al capturar

18 países con divisiones administrativas y autoridad ya mapeadas. Las URL de los presets son
**placeholders**: hay que poner la URL oficial real de la elección. Cuatro (Brasil, México,
Argentina, Honduras) tienen portal de datos abiertos confirmado; el resto usa `auto` y el
formato se resuelve al capturar. Una vez puesta la URL, la ingesta, el hashing y las 23+
reglas forenses funcionan igual que en Honduras.

### Nivel 2\* — Estados Unidos: cubrible, pero sin feed nacional único

**EE.UU. (`US`)** sí es cubrible — de hecho el tope de 100 endpoints se diseñó como "2× los
50 estados". Pero **no existe un portal federal único** de resultados en tiempo real: cada
Secretario de Estado publica por su cuenta, en formatos mixtos (JSON/CSV/HTML), y el feed
rápido agregado es **comercial** (AP/Edison). Implicaciones prácticas:

- 51 endpoints (50 estados + nacional). Si se apuntaran todos a un mismo host, el intervalo
  se estiraría a **6m23s**; repartidos por estado (lo natural, cada uno su propio dominio),
  se mantienen los **3 min**.
- El operador debe proveer la URL por estado. Los estados que publican HTML necesitan el
  parser HTML (detectado, pendiente de implementar); los que publican JSON/CSV funcionan hoy.
- Sin un acuerdo con AP/Edison, la cobertura "instantánea" nacional no es posible por diseño
  del sistema electoral de EE.UU., no por límite de VIGIL.

### Nivel 3 — Preset existe, sin portal público de resultados

**Cuba (`CU`)** y **Haití (`HT`)**: se pueden seleccionar, pero hoy no hay feed público de
resultados en tiempo real que monitorear.

---

## Notas sobre los límites

- **Piso ético inquebrantable: 3 minutos.** Solo `CENTINEL_CEILING_UNLOCKED=1` (ritual de
  emergencia del panel `/ops`, preset "Apagón / Crítico") lo baja — y aun así el
  presupuesto por host se sigue respetando; nunca se abusa del servidor ajeno.
- **Capacidad tope: 100 endpoints** (`MAX_ENDPOINTS`). Configuraciones mayores se truncan
  con warning. Es el doble de los 50 estados de EE.UU.: suficiente para cualquier país.
- **Por qué algunos superan los 3 min en un host:** con >24 endpoints en un solo host,
  mantener 3 min excedería 480 req/h. El sistema estira el intervalo lo mínimo necesario y lo
  registra en logs y en `data/latest_cycle.json`. Repartidos en varios hosts (≤24 por host),
  vuelven a 3 min — por eso EE.UU. (50 estados en 50 dominios) se mantiene en 3 min en la práctica.
- **Formato:** JSON y CSV tienen parser real y completo. XML/HTML se detectan pero su parser
  está pendiente; PDF (actas escaneadas) requiere OCR, fuera de alcance por ahora.
- **Fuentes:** política de rate limit en [`config/prod/rate_limiter.yaml`](../../config/prod/rate_limiter.yaml)
  y [`docs/RATE_LIMITING.md`](../RATE_LIMITING.md); presets en
  [`src/centinel/countries.py`](../../src/centinel/countries.py).

> Tabla generada a partir de los presets reales de `countries.py` y de la función
> `resolve_safe_interval`. Para regenerarla tras cambiar divisiones o el techo de rate
> limit, recalcular con `endpoints = divisiones + 1` e
> `intervalo = max(180, ⌈endpoints × 3600 / techo_rph⌉)`.
