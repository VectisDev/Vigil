# Cobertura por país — endpoints, formato y cadencia real

> Referencia rápida de lo que VIGIL puede monitorear hoy, por país.
> Los números de intervalo son **los que el poller impone automáticamente**
> (`resolve_safe_interval` en `src/centinel/core/poller_async.py`), no aspiraciones.

## Cómo leer esta tabla

- **Endpoints** = 1 nacional + N divisiones administrativas (departamentos / estados /
  provincias / regiones según el país). Es lo que se consulta por ciclo.
- **Formato**: `json` fijado por preset (validado); `auto` = se detecta por contenido
  (JSON o CSV) en la primera captura, sin escribir código.
- **Intervalo mínimo** = el piso que el sistema aplica solo, calculado como
  `max(180 s, ⌈endpoints × 3600 / 480⌉)`. El **piso ético es 3 min**; se estira
  automáticamente cuando los endpoints de un mismo host superarían el techo de
  **480 requests/hora/host**. Todos los endpoints de un país suelen estar en un
  solo host → ese es el caso mostrado (el más conservador).
- **req/h**: carga real contra el servidor de la autoridad a ese intervalo. Siempre ≤ 480.

Los tres niveles (Tier) reflejan el estado real de validación — ver
[README → Supported Countries](../../README.md#supported-countries).

---

## Tier 1 — Validado en producción

| País | Formato | Endpoints | Intervalo mín. | req/h | Autoridad |
|------|---------|-----------|----------------|-------|-----------|
| 🇭🇳 Honduras (`HN`) | `json` | 19 | 3m | 380 | Consejo Nacional Electoral (CNE) |

Honduras corrió en la elección general de 2025 con endpoints reales; dataset anclado a
Bitcoin (OpenTimestamps). 19 endpoints en un host → los 3 minutos se sostienen holgados.

## Tier 2 — Listos; el operador provee la URL, el formato se detecta al capturar

Divisiones administrativas y autoridad ya mapeadas. Las URL de los presets son
placeholders: hay que poner la URL oficial real de la elección. Ordenados por endpoints.

| País | Formato | Endpoints | Intervalo mín. | req/h | Autoridad |
|------|---------|-----------|----------------|-------|-----------|
| 🇨🇴 Colombia (`CO`) | `auto` | 34 | 4m15s | 480 | Registraduría Nacional |
| 🇲🇽 México (`MX`) | `auto` | 33 | 4m8s | 479 | Instituto Nacional Electoral (INE / PREP) |
| 🇩🇴 Rep. Dominicana (`DO`) | `auto` | 33 | 4m8s | 479 | Junta Central Electoral (JCE) |
| 🇧🇷 Brasil (`BR`) | `auto` | 28 | 3m30s | 480 | Tribunal Superior Eleitoral (TSE) |
| 🇵🇪 Perú (`PE`) | `auto` | 26 | 3m15s | 480 | JNE / ONPE |
| 🇻🇪 Venezuela (`VE`) | `auto` | 25 | 3m8s | 479 | Consejo Nacional Electoral (CNE) |
| 🇪🇨 Ecuador (`EC`) | `auto` | 25 | 3m8s | 479 | Consejo Nacional Electoral (CNE) |
| 🇦🇷 Argentina (`AR`) | `auto` | 25 | 3m8s | 479 | Cámara Nacional Electoral (CNE) |
| 🇬🇹 Guatemala (`GT`) | `auto` | 23 | 3m | 460 | Tribunal Supremo Electoral (TSE) |
| 🇺🇾 Uruguay (`UY`) | `auto` | 20 | 3m | 400 | Corte Electoral |
| 🇵🇾 Paraguay (`PY`) | `auto` | 19 | 3m | 380 | Tribunal Superior de Justicia Electoral |
| 🇳🇮 Nicaragua (`NI`) | `auto` | 18 | 3m | 360 | Consejo Supremo Electoral (CSE) |
| 🇨🇱 Chile (`CL`) | `auto` | 17 | 3m | 340 | Servicio Electoral (SERVEL) |
| 🇸🇻 El Salvador (`SV`) | `auto` | 15 | 3m | 300 | Tribunal Supremo Electoral (TSE) |
| 🇵🇦 Panamá (`PA`) | `auto` | 14 | 3m | 280 | Tribunal Electoral (TE) |
| 🇧🇴 Bolivia (`BO`) | `auto` | 10 | 3m | 200 | Tribunal Supremo Electoral (TSE) |
| 🇨🇷 Costa Rica (`CR`) | `auto` | 8 | 3m | 160 | Tribunal Supremo de Elecciones (TSE) |

## Tier 3 — Preset existe, sin portal público de resultados

| País | Formato | Endpoints | Intervalo mín. | req/h | Nota |
|------|---------|-----------|----------------|-------|------|
| 🇨🇺 Cuba (`CU`) | `auto` | 17 | 3m | 340 | No publica feed abierto de resultados |
| 🇭🇹 Haití (`HT`) | `auto` | 11 | 3m | 220 | Sin portal público estable |

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
