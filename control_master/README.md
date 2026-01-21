# Control Maestro

## Español

Esta carpeta es el **único lugar** que debes editar para configurar Sentinel en v5 sin tocar el resto del código.

Archivos editables:

1. `config.yaml` → configuración principal de scraping, reglas y fuentes.
2. `.env` → credenciales sensibles (claves, tokens).

### Pasos rápidos
1. Copia los ejemplos:
   ```bash
   cp control_master/config.yaml.example control_master/config.yaml
   cp control_master/.env.example control_master/.env
   ```
2. Ajusta valores según tu entorno.
3. Ejecuta los scripts con Poetry:
   ```bash
   poetry run python scripts/download_and_hash.py
   poetry run python scripts/analyze_rules.py
   ```

### Reglas
- **No modifiques** otros archivos fuera de esta carpeta.
- Esta carpeta es la fuente de verdad para configuración operativa.

---

## English

This folder is the **only place** you should edit to configure Sentinel v5 without touching the rest of the codebase.

Editable files:

1. `config.yaml` → main scraping configuration, rules, and sources.
2. `.env` → sensitive credentials (keys, tokens).

### Quick steps
1. Copy the examples:
   ```bash
   cp control_master/config.yaml.example control_master/config.yaml
   cp control_master/.env.example control_master/.env
   ```
2. Update values for your environment.
3. Run scripts with Poetry:
   ```bash
   poetry run python scripts/download_and_hash.py
   poetry run python scripts/analyze_rules.py
   ```

### Rules
- **Do not modify** files outside this folder.
- This folder is the source of truth for operational configuration.
