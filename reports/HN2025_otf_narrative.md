# Honduras 2025 — Análisis forense retroactivo

## Presidential election of 30 November 2025 · Retroactive forensic analysis

**Proyecto:** VIGIL · **Autor:** `VectisDev` · **Licencia:** AGPL-3.0
**Período cubierto:** 3–10 de diciembre de 2025 (64 capturas)
**Dataset:** `tests/fixtures/hnd_2025/` · DOI [10.5281/zenodo.20598892](https://doi.org/10.5281/zenodo.20598892)
**Raíz Merkle anclada a Bitcoin:** `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`

---

## Alcance y limitaciones — léase primero

Este documento describe un **análisis retroactivo post-mortem**, no una auditoría en vivo.
Las 64 capturas JSON del CNE fueron descargadas manualmente tras concluir el evento
electoral, y la cadena criptográfica se construyó **ex post** sobre los archivos ya
capturados. En consecuencia:

- La cadena y el anclaje OpenTimestamps prueban que **estos 64 archivos existían en esta
  forma en la fecha del anclaje**. No prueban custodia continua hora a hora durante el
  conteo, ni en qué momento el CNE publicó cada archivo.
- Las marcas de tiempo provienen del **nombre de archivo de la captura**, es decir del
  momento de descarga, no de un campo de publicación del CNE: el payload del CNE no
  incluye marca de tiempo propia. Los huecos entre capturas reflejan, al menos en parte,
  la ausencia del operador humano y no necesariamente interrupciones de la fuente.
- La captura continua en vivo es un objetivo operacional, no algo que este análisis
  demuestre.

**VIGIL no afirma fraude.** Registra observaciones verificables sobre datos publicados
públicamente y las entrega para evaluación humana independiente. La interpretación
corresponde a observadores calificados, tribunales y la opinión pública.

---

## Qué se observó

El análisis procesó 64 capturas del endpoint público del CNE entre el 3 y el 10 de
diciembre de 2025. Las observaciones siguientes son descriptivas: cada una es un hecho
comprobable contra el dataset, y ninguna establece causa ni intención.

### O1 · Cambio en el universo de actas

El campo `actas_totales` —el universo completo de actas a contabilizar— pasó de **19.152 a
19.167** (+15) entre capturas consecutivas el 8 de diciembre.

Un universo de referencia que cambia durante el conteo impide reconciliar totales entre
capturas anteriores y posteriores al cambio, y requiere explicación operativa de la fuente.
No se dispone de una; su ausencia no es por sí misma evidencia de irregularidad.

### O2 · Brechas de publicación

Se observaron intervalos en los que no se publicaron resultados actualizados mientras el
contador de actas divulgadas continuaba avanzando.

| Fecha | Último dato | Siguiente dato | Brecha | Δ actas |
|-------|-------------|----------------|--------|---------|
| 4 dic | 13:00 | 13:01 | 1 min | 0 |
| 4 dic | 14:00 | 14:01 | 1 min | 0 |
| 5 dic | 15:00 | 16:00 | 60 min | +8 |
| 6 dic | 17:00 | 18:00 | 60 min | 0 |
| 7 dic | 11:00 | 13:00 | 120 min | 0 |
| 7 dic | 18:00 | 19:00 | 60 min | 0 |

Alrededor de la brecha más extensa, la diferencia de votos entre el primer y el segundo
lugar pasó de **11.258 a 42.155** entre las capturas previa y posterior. Esto describe dos
observaciones y su diferencia; **no es una prueba causal** y no establece qué ocurrió
durante el intervalo.

Advertencia metodológica importante: parte de estas brechas corresponde a intervalos en que
el operador humano no estaba capturando. Separar silencio de la fuente de ausencia del
observador exige un registro de intentos de descarga, que este dataset retroactivo no
tiene. Es una capacidad del motor de captura continua, no de este análisis.

### O3 · Tasa de actas marcadas como inconsistentes

Desde la primera captura publicada el 3 de diciembre, **14,3% de las actas divulgadas**
aparecían marcadas como inconsistentes en el propio campo `actas_inconsistentes` del CNE.
La proporción se mantuvo en ese orden a lo largo del período observado.

Es un valor publicado por la fuente, no una inferencia de VIGIL. Cualquier extrapolación a
"votos afectados" es heurística, no forma parte de ninguna alerta automática del motor, y
requiere análisis humano.

### O4 · Velocidad de resolución sobre el umbral pre-registrado

Se observó una tasa de resolución de actas inconsistentes de **39,15 actas/minuto**, frente
a un umbral operativo pre-registrado de **10 actas/minuto** — aproximadamente **3,9×** el
umbral.

El umbral es una heurística operativa documentada en
[`docs/research/THRESHOLD_PREREGISTRATION.md`](../docs/research/THRESHOLD_PREREGISTRATION.md),
no una medición de campo de la capacidad real del CNE. Su calibración empírica contra datos
históricos está pendiente. La observación indica que la tasa supera el umbral declarado; no
constituye una medición de imposibilidad física.

---

## Relevancia para otras elecciones

El análisis se realizó sobre datos publicados por la propia autoridad electoral. No
requirió acceso especial, filtraciones ni fuentes confidenciales: solo descargar los
archivos que el CNE publicó y aplicar pruebas estadísticas documentadas.

Eso hace el método aplicable a cualquier país que publique resultados en formato legible por
máquina. La guía de replicación está en
[`docs/operations/REPLICATION_GUIDE.md`](../docs/operations/REPLICATION_GUIDE.md).

---

## Estado actual del sistema

| Componente | Estado |
|---|---|
| Detectores estadísticos | 25 reglas registradas; 2 degradadas a informativas por tasa de falsos positivos |
| Pipeline de captura continua | Implementado (bucle interno de 3 min); piloto en vivo pendiente |
| Panel de visualización público | En línea (GitHub Pages) |
| Verificación offline | `verify/verify_chain.py`, solo biblioteca estándar |
| Anclaje Bitcoin (OpenTimestamps) | Integrado y confirmado para el dataset HN 2025 |
| Suite de pruebas | 88 archivos de prueba; CI ejecuta un subconjunto de humo |
| Licencia | GNU AGPL-3.0 |

**Lo que falta:**
1. Piloto operacional en vivo sobre un evento electoral real.
2. Revisión académica independiente (buscada; ninguna firmada a la fecha).
3. Cobertura de pruebas por regla: 23 de 25 reglas carecen de prueba de comportamiento
   dedicada.
4. Recalibración del modelo nulo de falsos positivos a escala departamental.

---

## Sobre la neutralidad de este análisis

VIGIL no determina quién ganó ni quién debería haber ganado. Reporta observaciones
verificables sobre datos oficiales publicados.

Los hallazgos son reproducibles: cualquier persona puede descargar los 64 archivos JSON del
repositorio, ejecutar los scripts de análisis y obtener los mismos resultados. El código
está bajo AGPL-3.0.

La neutralidad es una propiedad técnica verificable, no una declaración de intenciones: los
detectores operan sobre series numéricas y no tienen representación de partidos ni
candidatos. Los umbrales están pre-registrados y versionados en abierto, de modo que un
tercero puede comprobar que no fueron ajustados después de ver los datos.

---

## Reproducibilidad

```bash
# Reproducir el análisis completo sobre el dataset incluido
make reproduce-2025-audit

# O directamente
python scripts/forensic_hnd_2025.py
python scripts/calibrate_2025.py --data tests/fixtures/hnd_2025

# Verificar la cadena de hashes de forma independiente (solo stdlib)
python verify/verify_chain.py tests/fixtures/hnd_2025/
```

- **Datos brutos:** `tests/fixtures/hnd_2025/` — 64 archivos JSON, hashes SHA-256
  verificables, más `MERKLE_ROOT_HN2025.ots` (prueba OpenTimestamps).
- **Motor de detección:** `src/auditor/inconsistent_acts.py`
- **Metodología y umbrales:** [`docs/research/METHODOLOGY.md`](../docs/research/METHODOLOGY.md) ·
  [`docs/research/THRESHOLD_PREREGISTRATION.md`](../docs/research/THRESHOLD_PREREGISTRATION.md)
- **Falsos positivos:** [`docs/research/FALSE_POSITIVE_ANALYSIS.md`](../docs/research/FALSE_POSITIVE_ANALYSIS.md)
  y `docs/research/fp_results_500.json`. Dos reglas presentan tasas inaceptables sobre datos
  sintéticos limpios y están degradadas a informativas; el documento las identifica.

---

## Contacto

Divulgación de seguridad: GitHub Security Advisories en
[`VectisDev/Vigil`](https://github.com/VectisDev/Vigil), o `security@vectis.dev`.

La autoría pública se publica bajo el seudónimo `VectisDev` por seguridad del operador.
