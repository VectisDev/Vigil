# Electoral Audit HN  
### Vigilancia automatizada y transparente de datos electorales del CNE (Honduras)

Proyecto open-source para monitorear, registrar y auditar **datos públicos** del Consejo Nacional Electoral (CNE) de Honduras.

## Objetivo
- Capturar snapshots periódicos de datos públicos (JSON).
- Generar hashes criptográficos (SHA-256) para verificación de integridad.
- Calcular diffs numéricos entre actualizaciones.
- Detectar inconsistencias objetivas (cambios negativos, outliers, saltos anómalos).
- Publicar reportes neutrales y verificables.

## Principios
- **Solo números, solo hechos**
- Sin opiniones, sin acusaciones, sin interpretación política
- Todo es reproducible y auditable
- Código y datos 100% open-source

## Alcance
Este proyecto **no declara fraude** ni beneficia a ningún actor político.  
Su función es **documentar cambios en datos públicos**, de forma automática y transparente.

## Estado
- Fase de preparación
- Pruebas con datos históricos (elecciones 2025)
- Preparado para activarse desde el minuto cero en elecciones futuras (ej. 2029)

## Estructura
- `data/` – Snapshots JSON crudos
- `hashes/` – Hashes SHA-256
- `diffs/` – Reportes de cambios
- `scripts/` – Automatización en Python
- `reports/` – Informes agregados
- `.github/workflows/` – GitHub Actions

## Licencia
MIT

## Canales
- X: https://x.com/AuditHN_IA
- Telegram: (próximamente)
