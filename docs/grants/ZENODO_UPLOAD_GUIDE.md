# Guía de subida a Zenodo — Dataset HN 2025
# Zenodo Upload Guide — HN 2025 Dataset

**Acción requerida por:** Carlos Zelaya  
**Tiempo estimado:** 15 minutos  
**Resultado:** DOI citable para los 64 JSON del CNE

---

## Por qué Zenodo

Zenodo (CERN) asigna DOIs permanentes a datasets de investigación, gratuito,
institucional, y aceptado por OTF, NDI y revistas académicas como fuente de datos.
Una vez subido, el DOI aparece en la propuesta OTF y en el working paper de Devis.

---

## Pasos / Steps

### 1. Crear cuenta (si no tienes)
→ https://zenodo.org → "Sign up" → usar GitHub para vincular directamente

### 2. Crear el archivo ZIP del dataset

```bash
cd /ruta/al/repo/centinel
zip -r centinel_hnd2025_snapshots.zip \
  tests/fixtures/hnd_2025/ \
  --exclude "*.pyc"
```

Tamaño esperado: ~70 KB

### 3. Subir a Zenodo
→ https://zenodo.org/uploads/new  
→ "Drop files" → subir `centinel_hnd2025_snapshots.zip`

### 4. Completar metadatos (copiar exactamente)

| Campo | Valor a pegar |
|-------|---------------|
| **Title** | Honduras 2025 Presidential Election — CNE TREP Snapshots (64 JSON files) |
| **Authors** | CENTINEL Project |
| **Description** | 64 JSON snapshots captured from Honduras CNE TREP system during the count of the November 30, 2025 general elections (December 3-10, 2025). Includes national-level presidential results: candidate votes, actas totales/divulgadas/inconsistentes. Merkle root anchored to Bitcoin via OpenTimestamps: f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780. Collected and analyzed by CENTINEL (github.com/VectisDev/centinel). |
| **License** | Creative Commons Attribution 4.0 |
| **Resource type** | Dataset |
| **Keywords** | electoral forensics, Honduras, CNE, TREP, election data, open data, Benford law, cryptographic audit |
| **Related identifiers** | https://github.com/VectisDev/centinel (is supplemented by) |

### 5. Publicar y copiar el DOI

→ Click "Publish" → Zenodo asigna DOI instantáneamente (ej: `10.5281/zenodo.XXXXXXX`)

### 6. Actualizar el repo con el DOI

Una vez tengas el DOI, enviar mensaje para actualizar:
- `tests/fixtures/hnd_2025/README_DATASET.md` — línea `**DOI:** *(pending)*`
- `docs/research/FALSE_POSITIVE_ANALYSIS.md` — sección Referencias
- `README.md` — sección "What we've audited so far"

---

## Alternativa: Harvard Dataverse

Si prefieres Harvard Dataverse (más prestigio académico):
→ https://dataverse.harvard.edu → "Add Data" → mismo proceso

---
*Estimado: 15 minutos · Costo: $0 · Impacto: DOI citable en OTF + paper Devis*
