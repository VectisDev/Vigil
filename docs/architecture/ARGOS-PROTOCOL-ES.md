# Protocolo ARGOS — Cinco Capas de Defensa de Vigil

## Introducción

El sistema Vigil implementa el Protocolo ARGOS: cinco capas de defensa independientes. Cada una protege contra una clase específica de amenazas. Se ejecutan en paralelo, no dependen una de otra, y la mayoría son autónomas.

---

## 🐦 Cuervo — Memoria Distribuida

### Problema Resuelto
**Testigo único vulnerable:** Si solo hay un testigo capturando datos, un atacante que comprometa al testigo puede modificar todos los datos sin que nadie se entere.

### Solución
Implementar **gossip P2P entre testigos** (Corvid Broadcast):
- Cada testigo atestigua lo que vio: "Yo capturé merkle_root = abc123 a las 15:30"
- Envía atestación a testigos hermanos
- Si merkles divergen, todos lo saben en minutos, no horas
- Presencia de ≥2 testigos activos = consenso distribuido

### Indicadores
- `corvid_broadcast.py`: módulo que gestiona gossip
- `hashes/sibling_attestations/`: directorio de atestaciones recibidas
- Log: "Cuervo: Atestación recibida de testigo X"

### Costo
- Cero: solo código local + red simple (HTTP POST)
- Sin blockchain, sin servidores centrales

### Evaluación
✅ **Implementación SÓLIDA**
- Resuelve problema real (testigo único)
- Non-fatal: si hermano offline, sigue capturando
- Consenso por mayoría de merkles (2/3)

---

## 🦑 Pulpo — Tinta de Transporte

### Problema Resuelto
**MITM (Man-in-the-middle):** Un atacante en la red (ISP, router, café WiFi) intercepta datos en tránsito entre testigos.

### Solución
Implementar **cifrado de tránsito ChaCha20Poly1305**:
- Derivar clave de cifrado del checkpoint anterior (merkle_root)
- Cada mensaje entre testigos se cifra con esa clave
- Nadie ve contenido, solo ciphertext
- Clave es verificable offline (auditor puede reproducirla)

### Indicadores
- `transport_blind.py`: módulo de cifrado
- Mensajes en logs: `[ENCRYPTED: xxx bytes]`
- Clave derivada: `SHA256(previous_merkle_root)`

### Costo
- Cero: criptografía de librería estándar (cryptography.io)
- Sin servidores, sin servicios externos

### Evaluación
✅ **Implementación EXCELENTE**
- Cifrado probado (ChaCha20Poly1305 usado por Signal, etc.)
- Derivación auditable (basada solo en datos públicos)
- Non-fatal: si cifrado falla, continúa sin cifrar (degradación)

---

## 🦌 Venado — retirado

Aquí se describía un protocolo de evasión de timing: jitter de ±30 %, un módulo
`evasion_scheduler.py` y **un 2 % de capturas señuelo con datos aleatorios**.

Nada de eso llegó a existir —ni el archivo ni la clave de configuración— y el
panel del operador lo mostraba como «ACTIVO», que era estado inventado.

Se retira, y los señuelos no vuelven. VIGIL publica capturas verificables: una
sola falsa, puesta a propósito, le daría a cualquier adversario la forma de
desacreditar todas las demás. El porqué completo está en
[`docs/NO-EVASION.md`](../NO-EVASION.md).

---

## 🦎 Lagartija — Auto-Regeneración

### Problema Resuelto
**Rootkit local:** Un atacante que logra acceso SSH/root al testigo puede modificar archivos del sistema (ej: cambiar código de captura, falsificar datos).

### Solución
Implementar **sync nightly con mirrors + detección de divergencia**:
- Cada noche, el testigo compara merkle_root local vs. mirrors remotos
- Si hay divergencia → significa datos locales fueron modificados
- Restaura desde mirror más confiable (mayoría)
- Logs exhaustivos de divergencia en `attack_log.jsonl`

### Indicadores
- `regeneration.py`: módulo de sync
- Mirror locations: `advanced_security_config.yaml`
- Log de divergencia: "Lagartija: divergencia detectada, restaurando..."
- Archivo de backup: `.archive/corrupted_chain_backup.json`

### Costo
- Cero: si mirrors son en Google Drive / Dropbox / AWS S3 gratuito
- Costo opcional: ~$5/mes si el almacenamiento tiene costo

### Evaluación
✅ **Implementación EXCELENTE**
- Detecta compromiso de forma **determinista** (merkle mismatch)
- Auto-restauración sin intervención humana
- Forensic: se guarda backup de datos comprometidos para auditoría

---

## ⚔️ Tejón — Kill Switch

### Problema Resuelto
**Ataque activo en tiempo real:** Un atacante está modificando datos en el preciso momento en que el testigo está capturando. El kill switch lo detecta y responde instantáneamente.

### Solución
Implementar **freeze autónomo + exponential backoff**:
1. **Detección de amenaza:** evaluate_threat() calcula puntuación (0–100)
   - Merkle divergence: +40 pts
   - Benford anomaly severa: +25 pts
   - Conectividad completa perdida: +20 pts
   - Consenso federation roto: +35 pts
   - **IGNORA:** cambios de endpoint (D11 se encarga)
   
2. **Congelación (si score ≥ 75):**
   - Snapshot atómico del estado actual
   - Crea lock file (`/tmp/vigil.lock`)
   - Deja de capturar nuevos datos
   - Registra todo en `attack_log.jsonl`

3. **Recuperación autónoma (exponential backoff):**
   - Intento 1: espera 2s ± 30% (1.4–2.6s)
   - Intento 2: espera 5s ± 30% (3.5–6.5s)
   - Intento 3: espera 10s ± 30% (7–13s)
   - Intento 4: espera 20s ± 30% (14–26s)
   - Intento 5+: espera 30s ± 30% (21–39s)

4. **Validación local (sin esperar hermanos):**
   - Verifica integridad de la cadena local
   - Compara contra mirrors locales
   - Si OK, resume operación normal
   - Si falla ≥5 veces, permanece congelado (seguro)

### Indicadores
- `kill_switch.py`: módulo principal
- Lock file: `/tmp/vigil.lock` (visible)
- Recovery state: `hashes/recovery_state.json`
- Attack events: `hashes/attack_log.jsonl` (JSONL append-only)

### Costo
- Cero: puro código local, cero dependencias

### Evaluación
✅ **Implementación CORRECTA**
- **Autónomo:** no espera a nadie para recuperarse
- **Defensivo:** freeze es "seguro de vida", no ataque
- **Moderado:** máximo 39s recuperación (electoral real)
- **Forensic:** auditor puede reconstruir timeline exacto desde logs

---

## Resumen Comparativo — Protocolo ARGOS

| Capa | Nombre | Amenaza | Mecanismo | Autonomía |
|------|--------|---------|-----------|-----------|
| D14 | 🐦 Cuervo | Testigo único | Gossip P2P | ✓ Autónoma |
| D15 | 🦑 Pulpo | MITM tránsito | Cifrado ChaCha20 | ✓ Autónoma |
| D17 | 🦎 Lagartija | Rootkit local | Sync mirrors | ✓ Autónoma |
| D18 | ⚔️ Tejón | Ataque activo | Freeze + backoff | ✓ Autónoma |

---

## Cómo Operar

### Ver Estado del Protocolo ARGOS
```bash
vigil panel
```

Salida esperada:
```
🐦 Cuervo (Memory):      ACTIVO ✓  Hermanos: 2/3
🦑 Pulpo (Encrypt):       ACTIVO ✓  Últimas encriptaciones: 2847
🦎 Lagartija (Healing):  ACTIVO ✓  Mirrors: 3/3 sincronizadas
⚔️ Tejón (Kill Switch):  READY    (no activado)
```

### Si Detectas Alerta Roja

1. **Leer logs:**
   ```bash
   tail -f hashes/attack_log.jsonl
   ```

2. **Identificar qué capa se activó:**
   - "Cuervo": hermanos reportan merkle diferente
   - "Pulpo": error de cifrado en tránsito
   - "Lagartija": divergencia en mirrors
   - "Tejón": congelamiento detectado

3. **Si Tejón (kill switch) activado:**
   ```bash
   cat /tmp/vigil.lock
   # Verá: reason, frozen_at, recovery_state
   ```

4. **Esperar recuperación o escalar:**
   - Tejón reintenta recuperación (ver en logs)
   - Si permanece congelado >5 minutos, contactar autoridad electoral
   - Proporcionar: `attack_log.jsonl`, `checkpoint_frozen.json`

---

## Configuración

### `advanced_security_config.yaml`

```yaml
defenses:
  corvid:
    enabled: true
    sibling_urls:
      - https://witness-b.example.com
      - https://witness-c.example.com
    gossip_interval_seconds: 60

  cephalopod:
    enabled: true
    cipher: "chacha20poly1305"
    key_derivation: "sha256(previous_merkle_root)"

  regeneration:
    enabled: true
    mirrors:
      - "s3://backup-bucket/centinel"
      - "https://drive.google.com/..."
    sync_hour_utc: 2  # Síncrono a las 2 AM

  kill_switch:
    enabled: true
    threat_threshold: 75
    benford_severity_threshold: 15.99
    backoff_schedule: [2, 5, 10, 20, 30]  # segundos base
    max_recovery_attempts: 5
```

---

## Referencias

- **D11:** Endpoint Monitor (detección de cambios de schema)
- **D12:** External Anchoring (Bitcoin OpenTimestamps)
- **D13:** Multi-Witness Federation (Byzantine consensus)
- **T1:** Chain integrity (Merkle hash chain)
- **T2:** Consensus (2/3 witnesses agree)
- **T3:** Timestamp independence (Bitcoin via OTS)
- **T4:** Federation (P2P no central authority)

---

**Última revisión:** 2026-06-18  
**Status:** Implementación v0.1 completa  
**Auditoría:** Listo para validación externa
