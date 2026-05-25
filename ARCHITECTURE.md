# Centinel — Arquitectura y parámetros permanentes

## Unidad de análisis: DEPARTAMENTO / ESTADO / PROVINCIA + NACIONAL

Centinel audita resultados electorales a nivel de división administrativa.

- 1 endpoint por departamento/estado/provincia + 1 endpoint nacional
- HN (18 departamentos): 19 endpoints
- SV (14 departamentos): 15 endpoints
- MX (32 estados): 33 endpoints
- AR (23 provincias + capital): 24 endpoints

Cada endpoint devuelve totales **agregados** de esa división completa: votos por candidato,
participación, actas escrutadas. Centinel nunca necesita datos de mesas/urnas individuales.

Las 5 reglas que usan el campo `mesas[]` operan sobre datos del JSON de HN que casualmente
incluye ese array dentro de la respuesta departamental. Para otros países ese campo simplemente
no existirá — esas reglas hacen skip limpio. Las 19 reglas matemáticas sobre totales
departamentales son el núcleo y aplican a cualquier país.

## Reglas estadísticas (24 reglas)

- **19 reglas matemáticas universales**: operan sobre totales departamentales — aplican a cualquier país
- **5 reglas mesa-level**: usan `mesas[]` del JSON de HN — hacen `return []` cuando el campo está ausente
- Umbrales configurables en `command_center/config.yaml` bajo `rules:`
- `country_overrides` permite umbrales por país sin tocar código
- Panel `/ops/` es la interfaz para ajustar umbrales por país

## Fuente de verdad de países

`src/centinel/countries.py` — `LATAM_COUNTRIES` dict con `CountryPreset` por código ISO.

## Costo: cero permanente

Todo corre en GitHub Actions gratuito. Sin servidores, sin bases de datos externas.

## Seguridad

- Seeds NUNCA en texto plano — solo hashes PBKDF2-SHA256 (600K iteraciones) en `web/access.json`
- El PDF generado en el wizard es el ÚNICO registro del seed en texto plano
- `*.pem` y `keys/` en `.gitignore` — nunca commitear claves privadas
- `DATA_REPO_TOKEN` nunca pasa por código del fork

## Red de federación

`src/centinel/federation/` — protocolo gossip P2P + consenso multi-testigo con tolerancia
bizantina ya implementados y 100% agnósticos al país. Bootstrap URL parametrizada por
`{country}` en `web/peers/{COUNTRY_CODE}.json`.
