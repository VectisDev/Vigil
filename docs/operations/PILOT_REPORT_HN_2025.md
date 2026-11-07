# Reporte Operacional — Análisis Retroactivo Honduras 2025
# Operational Report — Honduras 2025 Retroactive Analysis

**Documento:** RPT-CENTINEL-OPS-2025-HN-01  
**Fecha:** 2026-06-07  
**Versión:** 1.0  
**Datos fuente:** 64 archivos JSON originales del CNE, elecciones 30/11/2025  
**Período de publicación:** 2025-12-03 16:25 → 2025-12-10 17:03  
**Método:** Análisis retroactivo de archivos guardados a mano. La ficha única es [`docs/evidence/HN2025.md`](../evidence/HN2025.md).

---

## Declaración de método / Method Statement

Este reporte describe 64 archivos JSON del Consejo Nacional Electoral (CNE)
de Honduras, guardados a mano entre el 3 y el 10 de diciembre de 2025.
No son una cadena de hashes. No hay un registro de intentos de descarga.
Un intervalo entre dos nombres de archivo no demuestra que el portal estuviera
caído: puede ser un rato en el que nadie guardó un archivo. La nota de más
abajo ya lo dice.

Los números se leen como diferencias entre archivos guardados. La comparación
con 10 actas por minuto es una heurística del código, no un estudio
pre-registrado y no una capacidad humana medida.

---

## 1. Métricas operacionales / Operational Metrics

| Métrica | Valor |
|---------|-------|
| Total de capturas analizadas | 64 |
| Período cubierto | 7.0 días (168.6 horas) |
| Primera captura | 2025-12-03 16:25:27 |
| Última captura | 2025-12-10 17:03:59 |
| Intervalo mediano entre capturas | 60 minutos |
| Intervalo mínimo | 0.6 minutos |
| Intervalo máximo | **25.1 horas** |
| Gaps > 1 hora | 29 (46% de todos los intervalos) |
| Gaps > 4 horas | 10 |
| Intervalos > 10 h sin archivo guardado | **7** |
| Escrutinio final | 99.4% (19,052 / 19,167 actas) |
| Actas inconsistentes al cierre | 2,773 |

> **Nota sobre método de captura:** Las capturas del piloto 2025 fueron
> manuales, con intervalo mediano de 60 minutos. El sistema automatizado
> de VIGIL (≤5 minutos) no estaba activo en este período. Los intervalos
> largos coinciden con momentos en los que no hay un archivo guardado.
> No son una medición de que el portal estuviera caído.

---

## 2. Cronología completa de capturas / Complete Capture Timeline

| # | Fecha/hora | Actas div. | Incons. | Δ actas | Gap ant. (min) |
|---|------------|-----------|---------|---------|----------------|
| 1 | 03/12 16:25 | 15,310 | 2,189 | — | — |
| 2 | 03/12 17:00 | 15,314 | 2,189 | +4 | 35 |
| 3 | 03/12 18:00 | 15,341 | 2,196 | +27 | 60 |
| 4 | 03/12 19:00 | 15,353 | 2,198 | +12 | 60 |
| 5 | 03/12 20:00 | 15,378 | 2,199 | +25 | 60 |
| 6 | 03/12 21:00 | 15,393 | 2,202 | +15 | 60 |
| 7 | 03/12 22:00 | 15,419 | 2,209 | +26 | 60 |
| — | **SIN ARCHIVO 13.1h** | — | — | — | **786 min** |
| 8 | 04/12 11:06 | 15,565 | 2,296 | +146 | 786 |
| 9 | 04/12 12:00 | 15,600 | 2,327 | +35 | 54 |
| 10 | 04/12 13:00 | 15,630 | 2,345 | +30 | 60 |
| 11 | 04/12 14:00 | 15,680 | 2,367 | +50 | 60 |
| 12 | 04/12 14:00* | 15,682 | 2,367 | +2 | 0.6 |
| 13 | 04/12 15:00 | 17,010 | 4,713 | +1,328 | 60 |
| 14 | **04/12 16:00** | 17,782 | **2,367** | +772 | **60** ← resolución |
| 15 | 04/12 17:00 | 17,794 | 2,367 | +12 | 60 |
| — | **SIN ARCHIVO 19.1h** | — | — | — | **1,147 min** |
| 16 | 05/12 12:07 | 17,844 | 2,404 | +50 | 1,147 |
| … | *[ciclos 16-40 estancamiento]* | … | 2,404~2,407 | … | … |
| — | **SIN ARCHIVO 15.0h** | — | — | — | **903 min** |
| — | **SIN ARCHIVO 16.0h** | — | — | — | **960 min** |
| — | **SIN ARCHIVO 18.1h** | — | — | — | **1,086 min** |
| 62 | 09/12 16:00 | 19,024 | 2,773 | … | … |
| — | **SIN ARCHIVO 25.1h** | — | — | — | **1,508 min** |
| 64 | **10/12 17:03** | 19,052 | 2,773 | +28 | 1,508 |

---

## 3. Hallazgos forenses / Forensic Findings

### 3.1 Intervalo sin archivo guardado — 13.1 horas

| Campo | Valor |
|-------|-------|
| Inicio | 2025-12-03 22:00 |
| Fin | 2025-12-04 11:06 |
| Duración | **13.1 horas** (786 minutos) |
| Actas en backlog al inicio | 2,209 inconsistentes |
| Actas al reanudar | 2,296 inconsistentes (+87) |
| Diferencia de share entre los dos archivos | −0.504 pp en el share líder |

No hay un archivo guardado entre esas dos marcas. Eso no demuestra que el
portal estuviera caído. La diferencia de −0.504 puntos es una resta entre dos
agregados guardados, no una prueba con un contraste declarado de antemano.

### 3.2 Tasa entre dos archivos, comparada con una heurística

| Campo | Valor |
|-------|-------|
| Evento | 2025-12-04 15:00 → 16:00 |
| Actas inconsistentes resueltas | **2,346** |
| Tiempo transcurrido | 60 minutos |
| Tasa de resolución | **39.15 actas/min** |
| Heurística en el código | 10 actas/min |
| Comparación | cerca de 3.9× esa heurística |

39.15 es el delta dividido por 60. El 10 del código es una heurística
(`DEFAULT_MAX_RESOLUTION_RATE`). No es una capacidad humana medida y no es
un resultado pre-registrado. Ver [`docs/evidence/HN2025.md`](../evidence/HN2025.md).

### 3.3 Estancamiento prolongado de inconsistencias [ALTO]

**Evento mayor:** 25 ciclos consecutivos sin variación en actas inconsistentes.

| Campo | Valor |
|-------|-------|
| Inicio | 2025-12-05 17:00 |
| Fin | 2025-12-07 19:00 |
| Ciclos sin cambio | **25 consecutivos** |
| Actas inconsistentes congeladas | 2,407 |
| Duración total del estancamiento | ~50 horas |

**Evento menor:** 5 ciclos (2025-12-05 12:07 → 16:00), 2,404 inconsistentes.

Regla VIGIL aplicada: `irreversibility` — detecta cuando el backlog
de actas inconsistentes permanece estático mientras el escrutinio avanza.

### 3.4 Inyección progresiva — 17 ciclos [ALTO]

17 intervalos entre archivos guardados con Δactas < 100 mientras el conteo de
inconsistentes seguía por encima de 1,000. Es una descripción de la serie
guardada, no una atribución de intención.

| Muestra | Δ actas publicadas | Backlog inconsistentes |
|---------|--------------------|------------------------|
| 03/12 16:25→17:00 | +4 | 2,189 |
| 03/12 17:00→18:00 | +27 | 2,189 |
| 03/12 18:00→19:00 | +12 | 2,196 |
| 03/12 19:00→20:00 | +25 | 2,198 |

### 3.5 Siete intervalos largos sin archivo guardado

| # | Inicio | Fin | Duración |
|---|--------|-----|----------|
| 1 | 03/12 22:00 | 04/12 11:06 | **13.1 h** |
| 2 | 04/12 17:00 | 05/12 12:07 | **19.1 h** |
| 3 | 05/12 17:00 | 06/12 04:00 | **11.0 h** |
| 4 | 06/12 20:00 | 07/12 11:00 | **15.0 h** |
| 5 | 07/12 19:00 | 08/12 11:00 | **16.0 h** |
| 6 | 08/12 17:00 | 09/12 11:03 | **18.1 h** |
| 7 | 09/12 16:00 | 10/12 17:03 | **25.1 h** |

Esos siete intervalos caen de tarde a la mañana siguiente. El propio reporte
dice que en este piloto nadie estaba guardando archivos de noche. No son
una medición de caída del portal.

---

## 4. Estado final del escrutinio / Final Scrutiny State

| Métrica | Valor |
|---------|-------|
| Actas totales | 19,167 |
| Actas divulgadas | 19,052 |
| **Escrutinio** | **99.4%** |
| Actas inconsistentes al cierre | **2,773** |
| Actas inconsistentes / actas divulgadas | **14.6%** |

El proceso cerró con 14.6% de actas divulgadas clasificadas como inconsistentes,
sin resolución documentada en los datos disponibles.

---

## 5. Reproducibilidad / Reproducibility

```bash
# Pasos canónicos, sin dependencias del proyecto. Ver docs/VERIFY.md.
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make replay-offline
```

---

## 6. Metodología de detección / Detection Methodology

| Regla VIGIL | Config key | Hallazgo detectado |
|----------------|------------|-------------------|
| Saltos entre snapshots | `snapshot_jump` | Resolución 39.15 actas/min |
| Irreversibilidad estadística | `irreversibility` | Estancamiento 25 ciclos |
| Anomalía de participación | `participation_anomaly` | Inyección progresiva |
| Velocidad de procesamiento | `processing_speed` | 39.15/min contra la heurística de 10 |
| Mesas duplicadas/desaparecidas | `mesas_diff` | Intervalos sin archivo guardado |

---

*VIGIL — AGPL-3.0 — RPT-CENTINEL-OPS-2025-HN-01 v1.0*  
*Análisis generado automáticamente por el motor VIGIL dev-v12*  
*Los datos fuente (64 JSON) están en `tests/fixtures/hnd_2025/`*
