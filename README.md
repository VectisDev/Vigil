# [!] HND_SENTINEL_2029
### > EVERYTHING IS CONNECTED. THE DATA IS THE TRUTH.
### > TODO ESTÁ CONECTADO. LOS DATOS SON LA VERDAD.

---

## [EN] ENGLISH SECTION

### TECHNICAL MANIFESTO
**STATUS:** `OPERATIONAL`  
**SYSTEM:** `INDEPENDENT_INTEGRITY_AUDIT`  
**TARGET:** `CNE_PUBLIC_DATA_STREAM (HND)`

#### OBJECTIVE
Autonomous monitoring and cryptographic verification of public electoral data, focused exclusively on the presidential level across Honduras' 18 departments.
- **DATA_CAPTURE:** Periodic snapshots of JSON source streams.
- **INTEGRITY:** SHA-256 cryptographic signatures for immutable record-keeping.
- **FORENSICS:** Real-time detection of numerical anomalies, negative deltas, and outliers.
- **TRANSPARENCY:** Automated reporting of verifiable facts.

#### OPERATIONAL_PRINCIPLES
1. **NULL_INTERPRETATION:** Only numbers. No opinions. No political bias.
2. **IMMUTABILITY:** Once a hash is generated, the record is permanent.
3. **AUTONOMY:** Automated execution via GitHub Actions.
4. **ALGORITHMIC_NEUTRALITY:** The monitoring engine treats all Candidate_IDs as equal nodes. Thresholds are applied universally without human intervention.

#### SCOPE
This system is not a political tool. It does not declare outcomes. It documents **data mutations** in public streams at the presidential level for each of the 18 departments. The verdict belongs to the observers.

#### INDEPENDENT_VERIFICATION
To verify the integrity of any snapshot manually, use the following command:  
`sha256sum data/snapshot_YYYYMMDD_HHMM.json`  
Compare the output with the corresponding file in `hashes/`. If the strings match, the data is authentic.

#### PRINCIPAL SCRIPTS
- `scripts/download_and_hash.py`: Captures snapshots and generates SHA-256 hashes.
- `scripts/calculate_diffs.py`: Computes numerical differences between snapshots.
- `scripts/post_to_telegram.py`: Sends automated updates to Telegram (conditional on anomalies).
- Script Integrity: SHA-256 hashes of all scripts are committed in `hashes/scripts_hashes.md`. Verify any fork against the original to prevent manipulation. Disclaimer: Modifications in forks are not endorsed by the Sentinel.

#### EXPECTED ENDPOINTS (PREPARATION FOR 2029)
Based on historical patterns from 2025 elections, the Sentinel will monitor public endpoints like:  
- `https://resultadosgenerales2029.cne.hn/api/v1/results?level=presidencial&dept=01` (example for Presidential level, Atlántida department).  
- Parameters: `level` (PD for Presidential), `dept` (01-18 for departments).  
- Verification: Each snapshot will be hashed and committed. Use `sha256sum` to verify integrity locally.  
- Note: Endpoints will be updated when CNE 2029 site is active. Contributions welcome for endpoint discovery.

#### HOW TO CONTRIBUTE
- Fork the repo and test the scripts.  
- Open issues for technical suggestions.  
- Verify hashes and reports for independent auditing.

#### LICENSE
MIT

#### CHANNELS
- **X:** `[ENCRYPTED_CHANNEL_PENDING]`  
- **TELEGRAM:** `[ENCRYPTED_CHANNEL_PENDING]`

**The Sentinel watches. Data exposed. Verify or ignore.**  
**El Sentinel observa. Datos expuestos. Verifica o ignora.**

---

## [ES] SECCIÓN EN ESPAÑOL

### MANIFIESTO TÉCNICO
**ESTADO:** `OPERATIVO`  
**SISTEMA:** `AUDITORÍA_DE_INTEGRIDAD_INDEPENDIENTE`  
**OBJETIVO:** `FLUJO_DE_DATOS_PÚBLICOS_CNE (HND)`

#### OBJETIVO
Monitoreo autónomo y verificación criptográfica de datos electorales públicos, enfocado exclusivamente en el nivel presidencial para los 18 departamentos de Honduras.
- **CAPTURA_DATOS:** Snapshots periódicos de flujos JSON.
- **INTEGRIDAD:** Firmas criptográficas SHA-256 para registros inmutables.
- **FORENSE:** Detección en tiempo real de anomalías numéricas y deltas negativos.
- **TRANSPARENCIA:** Publicación automatizada de hechos verificables.

#### PRINCIPIOS_OPERATIVOS
1. **INTERPRETACIÓN_NULA:** Solo números. Sin opiniones. Sin sesgo político.
2. **INMUTABILIDAD:** Una vez generado el hash, el registro es permanente.
3. **AUTONOMÍA:** Ejecución automatizada vía GitHub Actions.
4. **NEUTRALIDAD_ALGORÍTMICA:** El motor trata todos los ID_Candidato como nodos iguales. Los umbrales se aplican universalmente sin intervención humana.

#### ALCANCE
Este sistema no es una herramienta política. No declara resultados. Documenta **mutaciones de datos** en flujos públicos al nivel presidencial para cada uno de los 18 departamentos. El veredicto pertenece a los observadores.

#### VERIFICACIÓN_INDEPENDIENTE
Para verificar la integridad de cualquier snapshot manualmente, use el siguiente comando:  
`sha256sum data/snapshot_YYYYMMDD_HHMM.json`  
Compare el resultado con el archivo correspondiente en `hashes/`. Si las cadenas coinciden, los datos son auténticos.

#### SCRIPTS PRINCIPALES
- `scripts/download_and_hash.py`: Captura snapshots y genera hashes SHA-256.
- `scripts/calculate_diffs.py`: Calcula diferencias numéricas entre snapshots.
- `scripts/post_to_telegram.py`: Envía actualizaciones automáticas a Telegram (condicional a anomalías).
- Integridad de Scripts: Hashes SHA-256 de todos los scripts se commitean en `hashes/scripts_hashes.md`. Verifica cualquier fork contra el original para prevenir manipulaciones. Disclaimer: Modificaciones en forks no están respaldadas por el Sentinel.

#### ENDPOINTS ESPERADOS (PREPARACIÓN PARA 2029)
Basado en patrones históricos de elecciones 2025, el Sentinel monitoreará endpoints públicos como:  
- `https://resultadosgenerales2029.cne.hn/api/v1/results?level=presidencial&dept=01` (ejemplo para nivel Presidencial, departamento Atlántida).  
- Parámetros: `level` (PD para Presidencial), `dept` (01-18 para departamentos).  
- Verificación: Cada snapshot será hasheado y commiteado. Usa `sha256sum` para verificar integridad localmente.  
- Nota: Endpoints se actualizarán cuando el sitio CNE 2029 esté activo. Contribuciones bienvenidas para descubrimiento de endpoints.

#### CÓMO CONTRIBUIR
- Forkea el repo y prueba los scripts.
- Abre issues para sugerencias técnicas.
- Verifica hashes y reportes para auditoría independiente.

#### LICENCIA
MIT

#### CANALES
- **X:** `[ENCRYPTED_CHANNEL_PENDING]`  
- **TELEGRAM:** `[ENCRYPTED_CHANNEL_PENDING]`

**The Sentinel watches. Data exposed. Verify or ignore.**  
**El Sentinel observa. Datos expuestos. Verifica o ignora.**

---

**LICENSE:** MIT | **AUDIT_MODE:** ACTIVE
