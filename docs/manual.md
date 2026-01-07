# Manual de Configuración y Operación

## [ES] Español

### Requisitos
- Python 3.11+
- Dependencias: `requirements.txt`

### Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuración de scraping (CNE)
Crea o edita `config.yaml` en la raíz del repositorio:
```yaml
base_url: "https://<URL_DEL_ENDPOINT>"
timeout: 15
retries: 3
headers:
  User-Agent: "HND-SENTINEL-2029"
backoff_base_seconds: 1
backoff_max_seconds: 30
candidate_count: 10
required_keys: []
field_map:
  totals:
    valid_votes:
      - "estadisticas.distribucion_votos.validos"
    null_votes:
      - "estadisticas.distribucion_votos.nulos"
    blank_votes:
      - "estadisticas.distribucion_votos.blancos"
    total_votes:
      - "estadisticas.distribucion_votos.total"
  candidate_roots:
    - "resultados"

sources:
  - name: "Nacional"
    source_id: "NACIONAL"
    level: "PRES"
    scope: "NATIONAL"
  - name: "Atlántida"
    department_code: "01"
    level: "PD"
    scope: "DEPARTMENT"
```

También puedes usar variables de entorno:
- `BASE_URL`
- `TIMEOUT`
- `RETRIES`
- `HEADERS` (JSON en string)

Notas:
- `candidate_count` define el número esperado de candidatos (se ajusta si el JSON trae más).
- `required_keys` permite validar claves mínimas en la respuesta (si está vacío no se valida).
- `field_map` permite declarar rutas alternativas para totales y candidatos si el JSON cambia.

### Descarga y hash de datos
```bash
python scripts/download_and_hash.py
```
Salida:
- JSON crudos en `data/`
- hashes en `hashes/`
- JSON normalizados en `data/normalized/`

### Análisis de reglas y tendencias
```bash
python scripts/analyze_rules.py
```
Salida:
- `analysis_results.json`
- `analysis_results.parquet` (si hay soporte en el entorno)
- `anomalies_report.json`
- `reports/summary_es.txt` y `reports/summary_en.txt`
- `reports/sentinel.db` (SQLite con métricas y anomalías)

### Publicación en Telegram
Variables necesarias:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Ejemplo:
```bash
python scripts/post_to_telegram.py "Reporte técnico" "hashes/snapshot_XX.sha256" neutral
```

### Frecuencia sugerida
- Descarga: cada 1 hora
- Reportes: cada 1–3 horas
- Resumen diario: 1 vez al día

---

## [EN] English

### Requirements
- Python 3.11+
- Dependencies: `requirements.txt`

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Scraping configuration (CNE)
Create or edit `config.yaml` in the repository root:
```yaml
base_url: "https://<ENDPOINT_URL>"
timeout: 15
retries: 3
headers:
  User-Agent: "HND-SENTINEL-2029"
backoff_base_seconds: 1
backoff_max_seconds: 30
candidate_count: 10
required_keys: []
field_map:
  totals:
    valid_votes:
      - "estadisticas.distribucion_votos.validos"
    null_votes:
      - "estadisticas.distribucion_votos.nulos"
    blank_votes:
      - "estadisticas.distribucion_votos.blancos"
    total_votes:
      - "estadisticas.distribucion_votos.total"
  candidate_roots:
    - "resultados"

sources:
  - name: "Nacional"
    source_id: "NACIONAL"
    level: "PRES"
    scope: "NATIONAL"
  - name: "Atlántida"
    department_code: "01"
    level: "PD"
    scope: "DEPARTMENT"
```

You can also use environment variables:
- `BASE_URL`
- `TIMEOUT`
- `RETRIES`
- `HEADERS` (JSON string)

Notes:
- `candidate_count` sets the expected candidate count (it adapts if JSON provides more).
- `required_keys` validates minimum keys in the response (empty means no validation).
- `field_map` lets you declare alternative paths for totals/candidates if JSON changes.

### Data download and hashing
```bash
python scripts/download_and_hash.py
```
Outputs:
- Raw JSON in `data/`
- Hashes in `hashes/`
- Normalized JSON in `data/normalized/`

### Rules and trend analysis
```bash
python scripts/analyze_rules.py
```
Outputs:
- `analysis_results.json`
- `analysis_results.parquet` (if supported)
- `anomalies_report.json`
- `reports/summary_es.txt` and `reports/summary_en.txt`
- `reports/sentinel.db` (SQLite with metrics and anomalies)

### Telegram publishing
Required variables:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Example:
```bash
python scripts/post_to_telegram.py "Technical report" "hashes/snapshot_XX.sha256" neutral
```

### Suggested cadence
- Download: every 1 hour
- Reports: every 1–3 hours
- Daily summary: once per day
