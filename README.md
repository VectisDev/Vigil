# Proyecto C.E.N.T.I.N.E.L.
**Centinela Electrónico Neutral Transparente Íntegro Nacional Electoral Libre**

---

## Español

### ¿Qué es Sentinel?
Sentinel es un sistema técnico independiente para observar y auditar datos electorales públicos en Honduras. Registra, normaliza y verifica cambios en datos publicados para producir reportes técnicos reproducibles y trazables.

### ¿Por qué importa?
La integridad electoral requiere evidencia verificable. Sentinel aporta transparencia técnica mediante snapshots, hashes encadenados y análisis de anomalías con enfoque ciudadano y neutral.

### Marco legal y límites de operación (Honduras)
Este proyecto se sustenta en el derecho de acceso a la información pública y en la obligación de publicar información por medios electrónicos.

Referencias normativas principales:
- **Ley de Transparencia y Acceso a la Información Pública** (Decreto 170-2006, reformas Decreto 60-2022).
- **Art. 3 y 4:** Reconocen el derecho ciudadano a acceder a información pública.
- **Art. 5:** Establece la obligación de facilitar el acceso por medios electrónicos.

Alcance operativo:
- Sentinel opera con finalidad de auditoría técnica y evidencia reproducible.
- No interfiere con sistemas oficiales ni sustituye a autoridades electorales.
- No procesa datos personales; solo usa fuentes públicas.
- Aplica scraping defensivo y respetuoso para evitar sobrecargas.

### Estado actual
- **AUDIT ACTIVE**

### Control centralizado (v5)
En v5, el único punto de control editable es **`control_master/`**.

- `control_master/` es la fuente de verdad de configuración operativa.
- `command_center/` es legado de dev-v4 y no define el control real de v5. Sus archivos se mantienen como referencia histórica y para reglas heredadas, pero no son el panel activo.

### Componentes del repositorio
- **control_master/**: configuración operativa centralizada (v5).
- **command_center/**: legado de dev-v4 para reglas y prototipos de panel, no es el control real de v5.
- **centinel_engine/**: motor separado en Node.js para anclaje de hashes y pruebas de publicación en blockchain.

### Primeros pasos (5 minutos)
1. Instala dependencias con Poetry:
   ```bash
   poetry install
   ```
2. Configura fuentes:
   ```bash
   cp control_master/config.yaml.example control_master/config.yaml
   cp control_master/.env.example control_master/.env
   ```
3. Genera un snapshot inicial:
   ```bash
   poetry run python scripts/download_and_hash.py
   ```
4. Ejecuta el análisis:
   ```bash
   poetry run python scripts/analyze_rules.py
   ```

### Producción con Docker
- Construye la imagen:
  ```bash
  docker build -t centinel_engine .
  ```
- Levanta servicios (cron):
  ```bash
  docker compose up -d
  ```

### Enlaces destacados
- [Guía rápida](QUICKSTART.md)
- [Contribución](CONTRIBUTING.md)
- [Roadmap](ROADMAP.md)
- [Diario de desarrollo](https://github.com/userf8a2c4/sentinel/tree/dev-v3/Dev%20Diary)
- [Seguridad](Security.md)
- [Licencia: MIT](Security.md)

## Gestión de Secrets y Backup
Consulta las instrucciones de resguardo seguro en [docs/SECRETS_BACKUP.md](docs/SECRETS_BACKUP.md).

### Agradecimientos
Gracias a la comunidad cívica, periodistas de datos y personas voluntarias que promueven transparencia electoral con evidencia verificable.

---

## English

### What is Sentinel?
Sentinel is an independent technical system to observe and audit public electoral data in Honduras. It records, normalizes, and verifies changes in published data to produce reproducible, traceable technical reports.

### Why does it matter?
Electoral integrity needs verifiable evidence. Sentinel provides technical transparency through snapshots, chained hashes, and anomaly analysis with a neutral, civic-first focus.

### Legal basis and operating boundaries (Honduras)
This project is grounded in the right to access public information and the obligation to publish information through electronic means.

Primary legal references:
- **Law on Transparency and Access to Public Information** (Decree 170-2006, amended by Decree 60-2022).
- **Arts. 3 & 4:** Recognize the citizen right to access public information.
- **Art. 5:** Establishes the obligation to facilitate access through electronic means.

Operational scope:
- Sentinel operates for technical auditing and reproducible evidence.
- It does not interfere with official systems or replace electoral authorities.
- It does not process personal data; it only uses public sources.
- It applies defensive, respectful scraping to avoid overload.

### Current status
- **AUDIT ACTIVE**

### Centralized control (v5)
In v5, the only editable control point is **`control_master/`**.

- `control_master/` is the source of truth for operational configuration.
- `command_center/` is a dev-v4 legacy artifact and does not define the real v5 control. Its files remain as historical reference and for inherited rules, but it is not the active control panel.

### Repository components
- **control_master/**: centralized operational configuration (v5).
- **command_center/**: dev-v4 legacy rules and control-panel prototypes, not the real v5 control.
- **centinel_engine/**: separate Node.js engine for hash anchoring and blockchain publishing experiments.

### Quick start (5 minutes)
1. Install dependencies with Poetry:
   ```bash
   poetry install
   ```
2. Configure sources:
   ```bash
   cp control_master/config.yaml.example control_master/config.yaml
   cp control_master/.env.example control_master/.env
   ```
3. Generate a snapshot:
   ```bash
   poetry run python scripts/download_and_hash.py
   ```
4. Run the analysis:
   ```bash
   poetry run python scripts/analyze_rules.py
   ```

### Production with Docker
- Build the image:
  ```bash
  docker build -t centinel_engine .
  ```
- Start services (cron):
  ```bash
  docker compose up -d
  ```

### Key links
- [Quickstart guide](QUICKSTART.md)
- [Contributing](CONTRIBUTING.md)
- [Roadmap](ROADMAP.md)
- [Dev diary](https://github.com/userf8a2c4/sentinel/tree/dev-v3/Dev%20Diary)
- [Security](Security.md)
- [License](Security.md)

## Secrets management and backup
See the secure backup guide at [docs/SECRETS_BACKUP.md](docs/SECRETS_BACKUP.md).

### Thanks
Thanks to civic community members, data journalists, and volunteers advancing electoral transparency through verifiable evidence.
