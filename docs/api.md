# API Pública / Public API

## Español

La API pública de C.E.N.T.I.N.E.L. expone endpoints de solo lectura para
consultar snapshots, alertas y verificar la cadena de hashes.

### Endpoints

#### `GET /snapshots/latest`
Devuelve el snapshot más reciente almacenado.

#### `GET /snapshots/{snapshot_id}`
Devuelve un snapshot por su hash (`snapshot_id`). Responde con `404` si no existe.

#### `GET /hashchain/verify?hash=xxx`
Verifica si el hash existe y si la cadena es consistente. Responde:

```json
{
  "exists": true,
  "valid": true
}
```

#### `GET /alerts`
Devuelve alertas disponibles desde `data/alerts.json` o `alerts.log`.

### Ejecución

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Variables de entorno

- `SNAPSHOTS_DB_PATH`: ruta al SQLite de snapshots (default `data/snapshots.db`).
- `CORS_ORIGINS`: lista separada por comas o `*` para permitir CORS.

## English

The C.E.N.T.I.N.E.L. public API exposes read-only endpoints to query snapshots,
alerts, and hashchain verification.

### Endpoints

#### `GET /snapshots/latest`
Returns the most recent snapshot stored.

#### `GET /snapshots/{snapshot_id}`
Returns a snapshot by its hash (`snapshot_id`). Returns `404` if missing.

#### `GET /hashchain/verify?hash=xxx`
Verifies whether the hash exists and the chain is consistent. Response:

```json
{
  "exists": true,
  "valid": true
}
```

#### `GET /alerts`
Returns available alerts from `data/alerts.json` or `alerts.log`.

### Run

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Environment variables

- `SNAPSHOTS_DB_PATH`: path to the snapshots SQLite DB (default `data/snapshots.db`).
- `CORS_ORIGINS`: comma-separated list or `*` for CORS.
