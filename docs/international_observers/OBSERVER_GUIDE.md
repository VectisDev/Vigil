# CENTINEL — Guía Técnica para Observadores Internacionales
# CENTINEL — Technical Guide for International Observers

**Versión / Version:** 1.0 · **Fecha / Date:** 2026-06-07  
**Audiencia / Audience:** OEA · Carter Center · UE EOM · OSCE/ODIHR · IFES · NDI  
**Idiomas / Languages:** Español (primario) · English (secondary)

---

## 1. ¿Qué es CENTINEL? / What is CENTINEL?

CENTINEL es un sistema de software libre que captura, encadena criptográficamente y
analiza estadísticamente los datos que publica el Consejo Nacional Electoral (CNE)
durante las elecciones en Honduras. Está diseñado para ser usado por observadores
electorales, periodistas y ciudadanos **sin acceso especial, sin costo y sin
necesidad de cooperación del CNE**.

**Principio fundamental:** CENTINEL no afirma fraude. Detecta anomalías estadísticas
en datos públicos y proporciona prueba criptográfica de integridad para evaluación
humana independiente.

---

## 2. Qué puede y qué no puede hacer CENTINEL / Capabilities and limitations

### ✅ Lo que CENTINEL hace / What CENTINEL does

| Capacidad | Descripción |
|-----------|-------------|
| **Captura de datos** | Descarga automáticamente los JSONs del CNE cada 2-5 minutos |
| **Cadena criptográfica** | Cada captura está enlazada con SHA-256 — cualquier modificación rompe la cadena |
| **23 reglas forenses** | Detección automática de: apagones de comunicación, tasas imposibles, anomalías de Benford, inconsistencias aritméticas por mesa |
| **Prueba verificable** | `verify_chain.py` — cualquier tercero puede verificar la integridad offline sin instalar CENTINEL |
| **Anclaje Bitcoin** | OpenTimestamps: prueba temporal inmutable de que los datos existían antes de un momento dado |
| **Reproducibilidad** | Un solo comando reproduce toda la auditoría: `make reproduce-2025-audit` |

### ❌ Lo que CENTINEL NO hace / What CENTINEL does NOT do

- **No analiza actas físicas** — solo los datos JSON que el CNE publica en línea
- **No accede** a sistemas internos del CNE ni a ninguna red privada
- **No emite juicios políticos** ni favorecer a ningún partido o candidato
- **No reemplaza** la observación electoral institucional en mesas de votación
- **No es evidencia jurídica** por sí mismo — es evidencia técnica para evaluación experta

---

## 3. Cómo usar CENTINEL en campo / How to use CENTINEL in the field

### Opción A — Verificar la cadena (sin instalar nada)

El observador solo necesita Python 3.6+ (incluido en la mayoría de sistemas):

```bash
# Descargar el verificador standalone (sin dependencias)
curl -O https://raw.githubusercontent.com/VectisDev/centinel/main/verify/verify_chain.py

# Verificar un directorio de snapshots
python3 verify_chain.py /ruta/a/los/snapshots/

# Resultado esperado en cadena íntegra:
# ╔══════════════════════════════════════════════════╗
# ║  ✅  CHAIN INTEGRITY VERIFIED — CADENA ÍNTEGRA ║
# ╚══════════════════════════════════════════════════╝

# Resultado si hay manipulación:
# ⛔ CHAIN BREAK DETECTED at snapshot_0042.json
```

### Opción B — Ejecutar análisis completo

```bash
# Clonar (una vez)
git clone https://github.com/VectisDev/centinel.git
cd centinel

# Instalar dependencias (una vez)
pip install numpy scipy scikit-learn pandas

# Reproducir la auditoría del piloto Honduras 2025
make reproduce-2025-audit

# Los datos originales están en:
ls tests/fixtures/hnd_2025/   # 64 JSON del CNE
```

### Opción C — Desplegar para monitoreo en tiempo real

Ver [docs/guides/QUICKSTART.md](../guides/QUICKSTART.md) — 3 pasos, sin servidores, costo cero.

---

## 4. Cómo interpretar los reportes / How to interpret reports

### Niveles de severidad / Severity levels

| Nivel | Significado | Acción sugerida |
|-------|-------------|-----------------|
| 🔴 **CRITICAL** | Anomalía estadísticamente severa (p < 0.001) | Documentar, escalar, solicitar explicación al CNE |
| 🟡 **WARNING** | Anomalía moderada (p < 0.01) | Monitorear, cruzar con otros indicadores |
| 🔵 **INFO** | Señal estadística leve (p < 0.05) | Solo para registro y análisis posterior |
| ✅ **NOMINAL** | Sin anomalía detectable | — |

### Las 5 reglas más importantes para observadores

**1. Mutación de registros (Rule 21 — mesa_reconciliation)**
Detecta cambios en los datos de mesas ya publicadas mediante SHA-256 por mesa.
Si se dispara: el CNE modificó datos que ya habían sido publicados y capturados.
*Esto es el indicador más directo de manipulación post-publicación.*

**2. Tasa de resolución imposible (Rule 15 — processing_speed)**
Detecta cuando las actas inconsistentes se resuelven a una velocidad mayor que
la capacidad humana plausible (~10 actas/minuto).
En HN 2025: 39.15 actas/min — 3.9× el umbral. Hallazgo verificable.

**3. Apagón de comunicación (Rule 14 — snapshot_jump)**
Detecta períodos donde el CNE deja de publicar datos. En HN 2025: 13.1 horas
el 3-4 de diciembre. Verificable con los timestamps de los archivos JSON.

**4. Imposibilidad aritmética por registro (Rule 22 — mesa_impossibility)**
Detecta cuando los datos por mesa son aritméticamente imposibles:
votos > inscritos, o candidatos > válidos. Error o manipulación interna.

**5. Aparición tardía de registros (Rule 23 — late_mesa)**
Detecta lotes grandes de nuevas mesas que aparecen cuando el escrutinio está
casi cerrado (≥90%). Señal de inyección tardía de datos.

---

## 5. Verificación de integridad criptográfica / Cryptographic integrity verification

### Verificar la cadena de hashes

Cada snapshot de CENTINEL incluye el hash SHA-256 del snapshot anterior.
Para verificar que ningún dato fue alterado después de la captura:

```bash
# Sin dependencias — solo Python 3.6+
python3 verify/verify_chain.py tests/fixtures/hnd_2025/

# Con verbose (muestra el hash de cada archivo)
python3 verify/verify_chain.py tests/fixtures/hnd_2025/ -v

# Guardar reporte
python3 verify/verify_chain.py tests/fixtures/hnd_2025/ -o reporte_verificacion.txt
```

### Verificar el anclaje en Bitcoin

Los 64 snapshots de HN 2025 fueron anclados a Bitcoin vía OpenTimestamps:

```bash
pip install opentimestamps-client
ots verify tests/fixtures/hnd_2025/MERKLE_ROOT_HN2025.ots
```

Merkle root (SHA-256 de los 64 archivos): `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`

Esto prueba que los 64 archivos existían antes de la fecha de anclaje en Bitcoin,
y que ninguno fue modificado después de ese momento.

---

## 6. Neutralidad y limitaciones / Neutrality and limitations

CENTINEL es políticamente neutral y metodológicamente transparente:

- **Código abierto** (AGPL-3.0): cualquier experto puede auditar la metodología
- **Reproducible**: los mismos datos + el mismo código = los mismos resultados
- **No afirma fraude**: reporta anomalías estadísticas para evaluación humana
- **Datos exclusivamente públicos**: analiza solo lo que el CNE publica en línea

**Limitaciones técnicas importantes para observadores:**

1. CENTINEL analiza los datos *publicados* por el CNE. Si el CNE publica datos
   incorrectos desde el origen, CENTINEL detectará las inconsistencias internas
   pero no puede detectar manipulaciones previas a la publicación.

2. Los hallazgos de CENTINEL son anomalías estadísticas. Su causa — error técnico,
   cambio metodológico, o manipulación intencional — requiere investigación adicional.

3. Los umbrales han sido calibrados contra datos de Honduras 2025. Para otros países
   o elecciones anteriores, pueden requerir recalibración.

---

## 7. Preguntas frecuentes de observadores / Observer FAQ

**¿Puedo citar los hallazgos de CENTINEL en un informe oficial de observación?**
Sí, con la aclaración de que son anomalías estadísticas en datos públicos del CNE,
no conclusiones sobre fraude. Citar como: *"El sistema CENTINEL detectó [hallazgo]
en los datos publicados por el CNE el [fecha]."*

**¿Cómo sé que CENTINEL no ha sido manipulado?**
El código fuente es público (github.com/VectisDev/centinel, AGPL-3.0). Cualquier
experto técnico puede auditar el código y reproducir los resultados desde los datos
originales del CNE con un solo comando.

**¿Funciona en otros países además de Honduras?**
Sí. CENTINEL tiene configuraciones para Guatemala, El Salvador, Nicaragua, México
y Colombia. Agregar un nuevo país requiere solo un archivo de configuración.

**¿Cuánto cuesta operar CENTINEL?**
Cero. Opera completamente en la capa gratuita de GitHub. No requiere servidores,
contratos de nube ni presupuesto operativo.

---

## 8. Contacto y recursos / Contact and resources

| Recurso | URL |
|---------|-----|
| Repositorio principal | https://github.com/VectisDev/centinel |
| Verificador de cadena | `verify/verify_chain.py` |
| Metodología estadística | `docs/research/METHODOLOGY.md` |
| Análisis de falsos positivos | `docs/research/FALSE_POSITIVE_ANALYSIS.md` |
| Convenciones estadísticas | `docs/stats/STATISTICAL_CONVENTIONS.md` |
| Reporte piloto HN 2025 | `docs/operations/PILOT_REPORT_HN_2025.md` |
| Matriz de cumplimiento OEA | `docs/standards/compliance_matrix.md` |

---

*CENTINEL — Software libre de auditoría electoral · AGPL-3.0*  
*Políticamente neutral · Reproducible · Verificable por cualquier tercero*  
*github.com/VectisDev/centinel*
