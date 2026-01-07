# QUICKSTART (5 minutos)

## Español
1. Clona el repo y entra al directorio:
   ```bash
   git clone <repo>
   cd sentinel
   ```
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. Configura archivos base:
   ```bash
   cp config.example.yaml config.yaml
   cp .env.example .env
   ```
4. Ajusta `config.yaml` (URL base, headers, fuentes).
5. Ejecuta la descarga y el análisis:
   ```bash
   python scripts/download_and_hash.py
   python scripts/analyze_rules.py
   ```
6. Lanza el dashboard:
   ```bash
   streamlit run dashboard.py
   ```

## English
1. Clone the repo and enter the directory:
   ```bash
   git clone <repo>
   cd sentinel
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. Set up base files:
   ```bash
   cp config.example.yaml config.yaml
   cp .env.example .env
   ```
4. Update `config.yaml` (base URL, headers, sources).
5. Run download + analysis:
   ```bash
   python scripts/download_and_hash.py
   python scripts/analyze_rules.py
   ```
6. Launch the dashboard:
   ```bash
   streamlit run dashboard.py
   ```
