# Emergency Procedures | Guía de Emergencia Centinel

**Version:** 1.0 | **Date:** 2026-05-18 | **Status:** Active

Documento de una sola página para actuar en 2 minutos bajo estrés.  
*One-page guide for action under stress in under 2 minutes.*

## Situaciones y acciones inmediatas

### 1) El sistema no responde en absoluto
**Qué verificar primero (comandos simples)**
- `docker ps`
- `python maintain.py status`

**Pasos exactos (copiar-pegar)**
1. `docker logs centinel-engine --tail 200`
2. `docker-compose down && docker-compose up -d`
3. `python maintain.py status`

**Dónde mirar logs**
- `docker logs centinel-engine --tail 200`
- `logs/` (si existe en el servidor)

**Cuándo y cómo activar modo pánico**
- Activa modo pánico si el servicio no responde tras un reinicio completo.
- Ejecuta: `python panic.py`

**Contactos de emergencia (si hay más personas)**
- Notifica al canal de alertas y al mantenedor/guardia en turno.

---

### 2) Recibo alertas críticas constantes
**Qué verificar primero (comandos simples)**
- `python maintain.py status`
- `docker logs centinel-engine --tail 200`

**Pasos exactos (copiar-pegar)**
1. `python maintain.py status`
2. `docker logs centinel-engine --tail 200`
3. `python maintain.py checkpoint-now`
4. Si persiste: `python panic.py`

**Dónde mirar logs**
- `docker logs centinel-engine --tail 200`
- Alertas en el canal de alertas

**Cuándo y cómo activar modo pánico**
- Si hay alertas críticas en bucle o degradación rápida.
- Ejecuta: `python panic.py`

**Contactos de emergencia (si hay más personas)**
- Escala al mantenedor principal y a seguridad/infra.

---

### 3) Sospecho ataque o bloqueo
**Qué verificar primero (comandos simples)**
- `python maintain.py status`
- `docker logs centinel-engine --tail 200`

**Pasos exactos (copiar-pegar)**
1. `python panic.py`
2. `docker logs centinel-engine --tail 200`
3. `python maintain.py checkpoint-now`
4. Aísla la máquina (bloquea tráfico entrante si aplica).

**Dónde mirar logs**
- `docker logs centinel-engine --tail 200`
- Logs del firewall/ingreso (si existen)

**Cuándo y cómo activar modo pánico**
- Inmediato ante sospecha razonable.
- Ejecuta: `python panic.py`

**Contactos de emergencia (si hay más personas)**
- Seguridad/infra, mantenedor principal, responsables legales si aplica.

---

### 4) Necesito pausar todo YA
**Qué verificar primero (comandos simples)**
- `python maintain.py status`

**Pasos exactos (copiar-pegar)**
1. `python panic.py`
2. `docker-compose down`

**Dónde mirar logs**
- `docker logs centinel-engine --tail 200`

**Cuándo y cómo activar modo pánico**
- Siempre que necesites detener todo de inmediato.
- Ejecuta: `python panic.py`

**Contactos de emergencia (si hay más personas)**
- Informa al canal de alertas y al mantenedor principal.

---

### 5) El servidor entero cayó
**Qué verificar primero (comandos simples)**
- Acceso SSH/VM/host
- Estado del proveedor (panel o CLI)

**Pasos exactos (copiar-pegar)**
1. Restablece la instancia/host.
2. `docker-compose up -d`
3. `python maintain.py status`

**Dónde mirar logs**
- Logs del proveedor (panel o CLI)
- `docker logs centinel-engine --tail 200`

**Cuándo y cómo activar modo pánico**
- Tras recuperar el host, si hay comportamiento anómalo.
- Ejecuta: `python panic.py`

**Contactos de emergencia (si hay más personas)**
- Infraestructura/proveedor y mantenedor principal.

---

### 6) Quiero restaurar desde backup
**Qué verificar primero (comandos simples)**
- Ubicación del último backup
- `python maintain.py status`

**Pasos exactos (copiar-pegar)**
1. Identifica el backup más reciente.
2. Restaura el backup según el procedimiento del proveedor.
3. `docker-compose up -d`
4. `python maintain.py status`

**Dónde mirar logs**
- Logs de restauración del proveedor
- `docker logs centinel-engine --tail 200`

**Cuándo y cómo activar modo pánico**
- Si la restauración no es confiable o hay corrupción.
- Ejecuta: `python panic.py`

**Contactos de emergencia (si hay más personas)**
- Mantenedor principal y responsable de backups.

---

## Comandos rápidos
```
python maintain.py status
python maintain.py checkpoint-now
python panic.py
docker-compose down && docker-compose up -d
docker logs centinel-engine --tail 200
```

## Datos críticos a mano
- URL del bucket de checkpoints: ________________________________
- Canal de alertas: ________________________________
- Ubicación del último backup conocido: ________________________________
- Contraseña/token de emergencia (o dónde encontrarla): ________________________________

---

**Nota final:**
> "Primero respira. No toques nada sin pensar. Todo está diseñado para poder recuperarse."

---

## English Summary — Emergency Procedures

This document is the operator's field guide for Centinel Engine incidents. Act within 2 minutes; escalate only after stabilizing.

### Quick Diagnostic

```bash
python maintain.py status          # service health
docker logs centinel-engine --tail 50  # recent logs (if using Docker)
```

### Scenario Matrix

| Symptom | Immediate action |
|---------|-----------------|
| System not responding | Restart via `docker-compose down && docker-compose up -d` or `make restart` |
| CNE API unreachable | Check network; the panel continues serving cached data from GitHub Pages |
| Hash chain broken | DO NOT continue. Preserve logs. Contact audit team before restarting |
| Missing snapshot | Check `data/snapshots/`; restore from last checkpoint in `data/temp/checkpoint.json` |
| Alerts storm | Verify if election data source changed; check `logs/anchors/` for chain continuity |

### Key Contacts

Fill before deployment:

| Role | Name | Contact |
|------|------|---------|
| Technical lead | ________ | ________ |
| Backup operator | ________ | ________ |
| UPNFM academic liaison | ________ | ________ |
| OTF program contact | ________ | ________ |

### Guiding Principle

> "Breathe first. Touch nothing without thinking. Everything is designed to be recoverable."
