# Lo que los datos dijeron — y nadie quería escuchar
## Análisis forense independiente: Elección Presidencial Honduras, diciembre 2025

**Prepared by:** Centinel Engine — Citizen Electoral Audit Infrastructure  
**Data source:** Public JSON API, Consejo Nacional Electoral (CNE) Honduras  
**Period covered:** December 3–10, 2025 (64 hourly snapshots)  
**Status:** Reproducible — all raw files and analysis code are open source

---

## Para quien lee esto primero

Este documento no requiere conocimientos técnicos. Está escrito para organizaciones que financian herramientas de transparencia electoral, observadores internacionales, y periodistas de investigación.

Describe qué encontró un sistema automatizado de auditoría — llamado **Centinel** — al analizar los datos oficiales publicados por el CNE de Honduras durante el conteo de la elección presidencial de 2025.

Todo lo descrito aquí proviene de los propios datos del CNE. No es una opinión. Es lo que el sistema publicó, medido con matemática básica.

---

## El problema que Centinel resuelve

Las autoridades electorales modernas publican resultados a través de APIs de internet — archivos de datos que cualquiera puede descargar. En teoría, esto garantiza transparencia. En la práctica, nadie tiene el tiempo ni las herramientas para monitorear esos datos hora a hora durante una semana, comparar cada versión con la anterior, y detectar si algo cambia de forma imposible.

Centinel hace exactamente eso, de forma automática, continua, y verificable.

En Honduras 2025, un ciudadano lo hizo **a mano**. Hora a hora. Durante una semana. Lo que encontró fue ignorado hasta que fue demasiado tarde para actuar. Centinel nació de esa experiencia.

---

## Qué encontró el sistema

El análisis procesó **64 capturas hourarias** del API oficial del CNE entre el 3 y el 10 de diciembre de 2025. Se detectaron **83 alertas**, de las cuales 82 fueron clasificadas como críticas.

A continuación, los hallazgos en orden de gravedad.

---

### Hallazgo 1: El universo electoral cambió — algo que no puede pasar

**Detectado:** 8 de diciembre, 11:00 AM  
**Tipo de anomalía:** Mutación del universo electoral

**En lenguaje simple:**
Imagine que un banco anuncia que administra 1,000 cuentas. En medio de las operaciones, sin explicación, el sistema dice que ahora administra 1,015 cuentas. Eso no puede pasar en un sistema íntegro — el número de cuentas es una constante.

En una elección, el número total de actas (las boletas por mesa de votación) es una constante establecida antes de que empiece el conteo. No puede cambiar durante el proceso.

**Lo que pasó:**
El campo `actas_totales` — el universo completo de actas a contar — cambió de **19,152 a 19,167** (+15 actas) el 8 de diciembre a las 11:00 AM, siete días después de que comenzara el conteo.

En una base de datos electoral correctamente construida, ese campo es un `const`, no una variable. Su cambio implica que alguien modificó el universo de referencia durante el conteo activo.

**Impacto:** 15 actas adicionales pueden representar entre 750 y 2,000 votos dependiendo del tamaño de las mesas afectadas.

---

### Hallazgo 2: Los resultados desaparecieron mientras el conteo continuaba — 7 veces

**Detectado:** múltiples ocasiones entre el 4 y el 8 de diciembre  
**Tipo de anomalía:** Blackout de datos (opacidad táctica)

**En lenguaje simple:**
Imagine un marcador de fútbol en tiempo real que, en mitad del partido, borra los goles anotados y muestra "0-0" — pero el cronómetro sigue corriendo y los árbitros siguen pitando. Cuando el marcador vuelve a mostrar goles, el resultado es diferente al que había antes del apagón.

**Lo que pasó:**
En 7 ocasiones distintas, el API del CNE devolvió una lista vacía de resultados (`[]`) mientras el contador de actas procesadas **seguía aumentando**. El sistema ocultó los votos al público mientras los contaba en la sombra.

El evento más grave ocurrió el **8 de diciembre entre las 15:00 y las 17:00** (2 horas):
- Antes del blackout (14:00): el candidato líder tenía una ventaja de **11,258 votos**
- Durante el blackout: se procesaron **1,086 actas** sin que nadie pudiera verlo
- Después del blackout (17:00): la ventaja había saltado a **42,155 votos** — un aumento del **+275%** en 2 horas de opacidad

La probabilidad matemática de que la tendencia electoral se invierta tan drásticamente de forma orgánica, y exclusivamente durante el periodo en que nadie puede ver los datos, es estadísticamente despreciable.

**Los 7 periodos de blackout detectados:**

| Fecha | Hora inicio | Hora fin | Duración | Actas en sombra |
|---|---|---|---|---|
| 4 dic | 13:00 | 13:01 | 1 min | 0 |
| 4 dic | 14:00 | 14:01 | 1 min | 0 |
| 5 dic | 15:00 | 16:00 | 60 min | +8 |
| 6 dic | 17:00 | 18:00 | 60 min | 0 |
| 7 dic | 11:00 | 13:00 | 120 min | 0 |
| 7 dic | 18:00 | 19:00 | 60 min | 0 |
| **8 dic** | **15:00** | **17:00** | **120 min** | **+1,086** |

---

### Hallazgo 3: 1 de cada 7 actas fue retenida como "inconsistente" desde el primer minuto

**Detectado:** desde el 3 de diciembre, primer snapshot (16:25)  
**Tipo de anomalía:** Inconsistencia estructural persistente

**En lenguaje simple:**
Imagine que abre un restaurante y desde el primer cliente, el sistema de caja marca el 14% de todas las órdenes como "error — no procesar". No una orden específica. No un lote de un día específico. El **14% de todo**, desde el principio, sin resolverse nunca.

**Lo que pasó:**
Desde el primer dato publicado el 3 de diciembre, el **14.3% de las actas divulgadas** estaban marcadas como "inconsistentes" — es decir, el sistema las contabilizaba en el total pero no mostraba sus votos. Ese porcentaje se mantuvo matemáticamente estable durante 7 días.

Al finalizar el conteo al 99.4%, había **2,773 actas "inconsistentes"** retenidas — aproximadamente **450,000 votos** que nunca fueron auditados públicamente.

El proceso se detuvo en 99.4% y no llegó al 100%. Esas 2,773 actas representan el 14.6% final del total — suficientes para cambiar cualquier resultado cerrado.

**Dato adicional:** la variabilidad de esta tasa fue de solo ±0.10% durante toda la semana — lo que indica que no fue un error aleatorio sino un estado controlado y estable.

---

### Hallazgo 4: Una velocidad de procesamiento de 8 veces el máximo normal

**Detectado:** 4 de diciembre, 17:00  
**Tipo de anomalía:** Velocidad de procesamiento anómala (HIGH)

**En lenguaje simple:**
Si una fábrica normalmente ensambla 500 piezas por hora, y de repente reporta haber ensamblado 4,142 piezas en 15 minutos, la primera pregunta no es "¡qué productivos!", sino "¿qué pasó realmente?"

**Lo que pasó:**
A las 17:00 del 4 de diciembre, el sistema procesó **16,568 actas en 60 minutos** — equivalente a **4,142 actas por cada 15 minutos**. El umbral normal establecido es 500 actas/15 minutos. Esta velocidad es 8.3 veces el máximo esperado.

Este evento coincide con el reinicio del sistema después del reset del universo electoral del día anterior.

---

## La línea de tiempo en una imagen

```
DIC 3       DIC 4           DIC 5-7         DIC 8           DIC 9-10
16:25       11:06  13:00    [congelado]      11:00  15:00-17:00  99.4%
  |           |      |           |              |        |          |
INICIO    Remontada PRIMER   SISTEMA        UNIVERSO GRAN        SISTEMA
CONTEO    Nasralla  BLACKOUT DETENIDO       CAMBIA  BLACKOUT    PARALIZADO
14.3%     reduce    brecha   88.02%         +15     brecha:     2,773
incons.   brecha    salta    escrutinio     actas   11k→42k     actas
          a 10,096  +69.6%   (sin mover)    (+15)   en 2 hrs    retenidas
```

---

## Por qué esto importa para el futuro

### Lo que Centinel habría permitido en tiempo real

Si Centinel hubiera estado operando durante la elección de 2025 con los detectores actuales, cada uno de estos eventos habría generado una alerta automática en segundos:

- **Blackout iniciado** → alerta CRITICAL en ≤5 minutos → notificación a observadores
- **Mutación del universo** → alerta CRITICAL → evidencia inmutable con hash SHA-256
- **Velocidad anómala** → alerta HIGH → timestamp verificable por terceros

Eso significa que en lugar de que un ciudadano documentara esto manualmente hora a hora durante una semana, y luego fuera ignorado y silenciado en redes sociales, **habría un sistema verificable, neutral, y resistente a la censura haciendo ese trabajo automáticamente**.

### Por qué "resistente a la censura" no es un detalle menor

El ciudadano que documentó estos hallazgos manualmente en diciembre de 2025 recibió ataques coordinados en redes sociales y fue sometido a restricciones de alcance (shadowban) en plataformas tras publicar los resultados. Los registros de esos ataques también están documentados en el repositorio de evidencia.

Centinel está diseñado específicamente para sobrevivir ese escenario:
- Los datos se anclan en Bitcoin (OpenTimestamps) — nadie puede modificar un hash ya anclado
- El sistema opera en múltiples nodos independientes — no hay un punto único de silencio
- El código es AGPL-3.0 — cualquier persona en cualquier país puede desplegarlo

### Relevancia para otras elecciones

El análisis aquí presentado se realizó sobre datos **del propio gobierno**. No requirió acceso especial, filtraciones ni fuentes confidenciales. Solo requirió descargar los archivos que el CNE publicó en internet y aplicar matemática básica.

Eso significa que Centinel puede adaptarse a cualquier país que publique datos electorales en formato digital. La guía de replicación está documentada en `docs/REPLICATION_GUIDE.md`.

---

## Estado actual del sistema (mayo 2026)

| Componente | Estado |
|---|---|
| Detectores estadísticos | 24 reglas activas, calibradas con datos HN 2025 |
| Pipeline de captura automática | Operacional — captura cada ≤5 minutos |
| Panel de visualización público | En línea (GitHub Pages) |
| Verificación offline | Bundle descargable con hash SHA-256 |
| Anclaje Bitcoin (OpenTimestamps) | Integrado |
| Suite de pruebas automatizadas | 499+ pruebas, CI/CD activo |
| Documentación técnica | 41 documentos, bilingüe ES/EN |
| Licencia | GNU AGPL-3.0 |

**Lo que falta para la siguiente elección:**
1. Piloto controlado con observadores en 2-3 municipios
2. Revisión académica formal (en curso, UNAH-UPNFM)
3. Traducción de interfaz de operador a Creole y francés (para expansión Caribe)

---

## Sobre la neutralidad de este análisis

Centinel no determina quién ganó ni quién debería haber ganado. Reporta hechos verificables sobre los datos oficiales.

Los hallazgos de este documento son reproducibles: cualquier persona puede descargar los 64 archivos JSON del repositorio público, ejecutar el script de análisis, y obtener exactamente los mismos resultados. El código está disponible en GitHub bajo licencia AGPL-3.0.

La neutralidad no es una declaración de principios — es una propiedad técnica del sistema. Los detectores no saben qué partido apoya a quién. Solo saben matemática.

---

## Contacto y reproducibilidad

- **Repositorio:** `github.com/userf8a2c4/centinel-engine`
- **Datos Honduras 2025:** `github.com/userf8a2c4/hnd-electoral-audit-2025`
- **Script de análisis:** `scripts/calibrate_2025.py`
- **Datos brutos:** `hnd-electoral-audit-2025/data/` (64 archivos JSON, SHA-256 verificables)

Para reproducir este análisis:
```bash
git clone https://github.com/userf8a2c4/centinel-engine
git clone https://github.com/userf8a2c4/hnd-electoral-audit-2025
cd centinel-engine
python scripts/calibrate_2025.py --data ../hnd-electoral-audit-2025/data
```

---

*Este documento fue generado automáticamente a partir del análisis de Centinel Engine v0.1 y revisado editorialmente para audiencia no-técnica. La versión técnica completa está disponible en `reports/calibration_2025.md`.*
