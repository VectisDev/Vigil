# Cobertura por país — endpoints, formato y cadencia real

> Referencia rápida de lo que VIGIL puede solicitar hoy, por país.
> Los números de intervalo son **los que el poller impone automáticamente**
> (`resolve_safe_interval` en `src/centinel/core/poller_async.py`), no aspiraciones.

## Cómo leer esta tabla

- **Endpoints** = 1 nacional + N divisiones administrativas (departamentos / estados /
  provincias / regiones según el país). Es lo que se consulta por ciclo.
- **Formato**: `json` fijado por preset (validado); `auto` = se detecta por contenido
  (JSON o CSV) en la primera captura, sin escribir código.
- **Intervalo mín.** = el piso que el sistema aplica solo, calculado como
  `max(180 s, ⌈endpoints × 3600 / 480⌉)`. El **piso ético es 3 min**; se estira
  automáticamente cuando los endpoints de un mismo host superarían el techo de
  **480 requests/hora/host**. Se asume todos los endpoints en un solo host (el caso
  más conservador).
- **req/h**: carga real contra el servidor de la autoridad a ese intervalo. Siempre ≤ 480.
- **Nivel**: estado de validación. **1** = validado en producción · **2** = listo, el
  operador provee la URL y el formato se detecta al capturar · **3** = preset existe pero
  no hay portal público de resultados.

---

## Lista completa — los 20 países que se pueden seleccionar

| # | País | Código | Formato | Endpoints | Intervalo mín. | req/h | Nivel | Autoridad electoral |
|----|------|--------|---------|-----------|----------------|-------|-------|---------------------|
| 1 | 🇦🇷 Argentina | `AR` | `auto` | 25 | 3m8s | 479 | 2 | Cámara Nacional Electoral (CNE) |
| 2 | 🇧🇴 Bolivia | `BO` | `auto` | 10 | 3m | 200 | 2 | Tribunal Supremo Electoral (TSE) |
| 3 | 🇧🇷 Brasil | `BR` | `auto` | 28 | 3m30s | 480 | 2 | Tribunal Superior Eleitoral (TSE) |
| 4 | 🇨🇱 Chile | `CL` | `auto` | 17 | 3m | 340 | 2 | Servicio Electoral (SERVEL) |
| 5 | 🇨🇴 Colombia | `CO` | `auto` | 34 | 4m15s | 480 | 2 | Registraduría Nacional del Estado Civil |
| 6 | 🇨🇷 Costa Rica | `CR` | `auto` | 8 | 3m | 160 | 2 | Tribunal Supremo de Elecciones (TSE) |
| 7 | 🇨🇺 Cuba | `CU` | `auto` | 17 | 3m | 340 | 3 | Consejo Electoral Nacional |
| 8 | 🇪🇨 Ecuador | `EC` | `auto` | 25 | 3m8s | 479 | 2 | Consejo Nacional Electoral (CNE) |
| 9 | 🇸🇻 El Salvador | `SV` | `auto` | 15 | 3m | 300 | 2 | Tribunal Supremo Electoral (TSE) |
| 10 | 🇬🇹 Guatemala | `GT` | `auto` | 23 | 3m | 460 | 2 | Tribunal Supremo Electoral (TSE) |
| 11 | 🇭🇹 Haití | `HT` | `auto` | 11 | 3m | 220 | 3 | Conseil Électoral Provisoire (CEP) |
| 12 | 🇭🇳 Honduras | `HN` | `json` | 19 | 3m | 380 | 1 | Consejo Nacional Electoral (CNE) |
| 13 | 🇲🇽 México | `MX` | `auto` | 33 | 4m8s | 479 | 2 | Instituto Nacional Electoral (INE / PREP) |
| 14 | 🇳🇮 Nicaragua | `NI` | `auto` | 18 | 3m | 360 | 2 | Consejo Supremo Electoral (CSE) |
| 15 | 🇵🇦 Panamá | `PA` | `auto` | 14 | 3m | 280 | 2 | Tribunal Electoral (TE) |
| 16 | 🇵🇾 Paraguay | `PY` | `auto` | 19 | 3m | 380 | 2 | Tribunal Superior de Justicia Electoral (TSJE) |
| 17 | 🇵🇪 Perú | `PE` | `auto` | 26 | 3m15s | 480 | 2 | Jurado Nacional de Elecciones (JNE) / ONPE |
| 18 | 🇩🇴 Rep. Dominicana | `DO` | `auto` | 33 | 4m8s | 479 | 2 | Junta Central Electoral (JCE) |
| 19 | 🇺🇾 Uruguay | `UY` | `auto` | 20 | 3m | 400 | 2 | Corte Electoral |
| 20 | 🇻🇪 Venezuela | `VE` | `auto` | 25 | 3m8s | 479 | 2 | Consejo Nacional Electoral (CNE) |

**Totales:** 20 países · 1 validado en producción (Nivel 1) · 17 listos para campo (Nivel 2) ·
2 sin fuente pública (Nivel 3). Endpoints por ciclo en toda la región: 424.

---

## Detalle por nivel de validación

### Nivel 1 — Validado en producción

**Honduras (`HN`)** corrió en la elección general de 2025 con endpoints reales; dataset
anclado a Bitcoin (OpenTimestamps). 19 endpoints en un host → los 3 minutos se sostienen
holgados. Formato JSON (TREP del CNE).

### Nivel 2 — Listos; el operador provee la URL, el formato se detecta al capturar

17 países con divisiones administrativas y autoridad ya mapeadas (AR, BO, BR, CL, CO, CR,
EC, SV, GT, MX, NI, PA, PY, PE, DO, UY, VE). Las URL de los presets son **placeholders**:
hay que poner la URL oficial real de la elección. Una vez puesta, la ingesta, el hashing y
las 23+ reglas forenses funcionan igual que en Honduras.

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
- **Por qué algunos superan los 3 min:** con >24 endpoints en un solo host, mantener 3 min
  excedería 480 req/h. El sistema estira el intervalo lo mínimo necesario y lo registra en
  logs y en `data/latest_cycle.json`. Si esos endpoints se repartieran en varios hosts
  (≤24 por host), volverían a 3 min.
- **Formato:** JSON y CSV tienen parser real y completo. XML/HTML se detectan pero su parser
  está pendiente; PDF (actas escaneadas) requiere OCR, fuera de alcance por ahora.
- **Fuentes:** política de rate limit en [`config/prod/rate_limiter.yaml`](../../config/prod/rate_limiter.yaml)
  y [`docs/RATE_LIMITING.md`](../RATE_LIMITING.md); presets en
  [`src/centinel/countries.py`](../../src/centinel/countries.py).

> Tabla generada a partir de los presets reales de `countries.py` y de la función
> `resolve_safe_interval`. Para regenerarla tras cambiar divisiones o el techo de rate
> limit, recalcular con `endpoints = divisiones + 1` e
> `intervalo = max(180, ⌈endpoints × 3600 / techo_rph⌉)`.
