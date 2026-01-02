# Electoral Audit HN
### Vigilancia automatizada y transparente de datos electorales del CNE (Honduras)

Proyecto open-source para monitorear, registrar y auditar **datos públicos** del Consejo Nacional Electoral (CNE) de Honduras.

## Español / Spanish

### Objetivo
- Capturar snapshots periódicos de datos públicos (JSON).
- Generar hashes criptográficos (SHA-256) para verificación de integridad.
- Calcular diffs numéricos entre actualizaciones.
- Detectar inconsistencias objetivas (ej. cambios negativos, outliers, saltos anómalos).
- Publicar reportes neutrales y verificables.

### Principios
- **Solo números, solo hechos**.
- Sin opiniones, sin acusaciones, sin interpretación política.
- Todo es reproducible y auditable.
- Código y datos 100% open-source.

### Alcance
Este proyecto **no declara fraude** ni beneficia a ningún actor político.  
Su función es **documentar cambios en datos públicos**, de forma automática y transparente.

### Estado
- Fase de preparación.
- Pruebas con datos históricos (elecciones 2025).
- Preparado para activarse desde el minuto cero en elecciones futuras (ej. 2029).

### Estructura
- `data/` – Snapshots JSON crudos.
- `hashes/` – Hashes SHA-256.
- `diffs/` – Reportes de cambios.
- `scripts/` – Automatización en Python.
- `reports/` – Informes agregados.
- `.github/workflows/` – GitHub Actions.

### Cómo Contribuir
- Forkea el repo y prueba los scripts.
- Abre issues para sugerencias técnicas.
- Verifica hashes y reportes para auditoría independiente.

### Licencia
MIT

### Canales
- X: https://x.com/AuditHN_IA  
- Telegram: (próximamente)

---

## English / Inglés

### Objective
- Capture periodic snapshots of public data (JSON).
- Generate cryptographic hashes (SHA-256) for integrity verification.
- Calculate numerical diffs between updates.
- Detect objective inconsistencies (e.g., negative changes, outliers, anomalous jumps).
- Publish neutral and verifiable reports.

### Principles
- **Only numbers, only facts**.
- No opinions, no accusations, no political interpretation.
- Everything is reproducible and auditable.
- Code and data 100% open-source.

### Scope
This project **does not declare fraud** nor benefit any political actor.  
Its function is to **document changes in public data**, automatically and transparently.

### Status
- Preparation phase.
- Testing with historical data (2025 elections).
- Ready to activate from minute zero in future elections (e.g., 2029).

### Structure
- `data/` – Raw JSON snapshots.
- `hashes/` – SHA-256 hashes.
- `diffs/` – Change reports.
- `scripts/` – Python automation.
- `reports/` – Aggregated reports.
- `.github/workflows/` – GitHub Actions.

### How to Contribute
- Fork the repo and test the scripts.
- Open issues for technical suggestions.
- Verify hashes and reports for independent auditing.

### License
MIT

### Channels
- X: https://x.com/AuditHN_IA  
- Telegram: (coming soon)
