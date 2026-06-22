# Centinel Performance Roadmap 2026

## Objetivo
Optimizar Centinel para soportar 1000+ nodos sin degradación de performance ni costos lineales.

---

## Fase 1: Diagnostics & Metrics (Inmediato - Q2 2026)

### 1.1 Telemetría de Performance
```python
# Agregar métricas en tiempo real:
- Latencia por ronda gossip (target: <500ms)
- Tamaño de forensic trail por elección (target: <1MB)
- CPU usage por validación (target: <100ms/nodo)
- Memory footprint por nodo (target: <50MB)
- Bandwidth per gossip round (target: <10MB)
```

**Archivos a modificar:**
- `src/centinel/swarm/gossip.py` → agregar telemetría
- `src/centinel/audit/validator.py` → medir validación

**Métrica de éxito:** Dashboard mostrando 95th percentile de cada métrica

---

## Fase 2: Forensic Trail Optimization (Q2-Q3 2026)

### 2.1 Log Rotation & Archival
```
Actual:
├── forensic_trail.log (crece infinito)
└── Problema: 8.7 MB/año sin límite

Propuesta:
├── forensic_trail_2026-06.log (30 días)
├── forensic_trail_2026-05.log.gz (comprimido)
├── forensic_archive_2026.db (PostgreSQL)
└── S3 backup (mensual)
```

**Implementación:**
```python
# src/centinel/audit/forensic.py
class ForensicLogger:
  def __init__(self, retention_days=30, archive_after=7):
    self.rotation_policy = RotationPolicy(
      max_size=100MB,
      max_age=retention_days,
      compress_after=archive_after,
      archive_to=PostgreSQL
    )
  
  def write_entry(self, event):
    # Auto-rotate si needed
    self.check_rotation()
    self.logger.write(event)
```

**Reducción de costos:**
- Almacenamiento: $20 → $3/mes (99% reducción)
- Backup: $50/mes → $5/mes
- **Total ahorro: $62/mes**

---

## Fase 3: Reputación Caching (Q3 2026)

### 3.1 Redis Cache Layer
```
Actual:
├── Cada validación recalcula Trust = (α+1)/(α+β+2)
├── 100 nodos × 5 validaciones/día = 500 cálculos/día
└── ~180,000 cálculos/año

Propuesta:
├── Cache en Redis con TTL=1 hora
├── Invalidate si α o β cambia >5%
└── 90% cache hit rate esperado
```

**Implementación:**
```python
# src/centinel/reputation/cache.py
class ReputationCache:
  def __init__(self, redis_client, ttl_seconds=3600):
    self.redis = redis_client
    self.ttl = ttl_seconds
  
  def get_trust(self, node_id):
    cached = self.redis.get(f"trust:{node_id}")
    if cached:
      return cached  # Miss: 0.1ms vs Hit: 100ms
    
    # Recalculate si needed
    trust = (node.alpha + 1) / (node.alpha + node.beta + 2)
    self.redis.setex(f"trust:{node_id}", self.ttl, trust)
    return trust
```

**Reducción de costos:**
- CPU computation: -90%
- **Total ahorro: $15-30/mes (menor cómputo)**

---

## Fase 4: Gossip Backpressure (Q3 2026)

### 4.1 Adaptive Fan-out
```
Actual:
├── Fan-out=3 (fijo)
├── Si N=100, 300 mensajes/ronda
├── En congestión = pérdida = más rondas
└── Peor caso: 10+ rondas (3,000 mensajes)

Propuesta:
├── Fan-out dinámico basado en latencia
├── Si latency > 200ms: fan-out=2
├── Si latency > 500ms: fan-out=1 (fallback)
└── Target: max 6 rondas siempre
```

**Implementación:**
```python
# src/centinel/swarm/gossip.py
class AdaptiveGossip:
  def calculate_fanout(self, round_metrics):
    avg_latency = round_metrics.avg_latency_ms
    
    if avg_latency < 100:
      return 3  # Normal
    elif avg_latency < 200:
      return 2  # Degraded
    else:
      return 1  # Crisis mode
  
  def gossip_round(self):
    fanout = self.calculate_fanout(self.metrics)
    # Only send to fanout peers
    targets = self.select_peers(fanout)
    self.broadcast(targets)
```

**Reducción de costos:**
- Bandwidth: -40% en congestión
- Latencia: -30% (menos rondas)
- **Total ahorro: $25-50/mes (menos mensajes)**

---

## Fase 5: Parallel Hash Verification (Q4 2026)

### 5.1 WebWorker Pool
```
Actual:
├── SHA-256 secuencial en main thread
├── Dataset 10MB = 5+ segundos
└── Bloquea consenso

Propuesta:
├── 4x WebWorkers en paralelo
├── Chunk dataset en 4 partes
├── ~1.5 segundos total (3x más rápido)
└── Main thread libre para otros cálculos
```

**Implementación:**
```python
# src/centinel/audit/validator.py
class ParallelValidator:
  def __init__(self, worker_count=4):
    self.workers = [Worker() for _ in range(worker_count)]
  
  async def verify_dataset(self, dataset, hashes):
    # Split en chunks
    chunks = [dataset[i::4] for i in range(4)]
    
    # Parallelizar
    results = await asyncio.gather(
      self.workers[0].verify(chunks[0]),
      self.workers[1].verify(chunks[1]),
      self.workers[2].verify(chunks[2]),
      self.workers[3].verify(chunks[3]),
    )
    
    return all(results)
```

**Reducción de costos:**
- CPU/validación: -70%
- Latencia: -66%
- **Total ahorro: $20-40/mes**

---

## Fase 6: Byzantine Optimization (Q4 2026)

### 6.1 Early Termination
```
Actual:
├── Siempre ejecuta log(N)+2 rondas
├── Incluso si consenso alcanzado en ronda 3
└── Desperdicio: hasta 50% de mensajes

Propuesta:
├── Detectar consenso alcanzado
├── Terminar gossip early
├── Mismo garantía matemática
└── Solo si >66% honestos validaron
```

**Reducción de costos:**
- Mensajes: -30% en promedio
- Latencia: -50%
- **Total ahorro: $30-60/mes**

---

## Resumen Financiero

| Fase | Optimización | Ahorro | Timeline |
|--|--|--|--|
| 1 | Telemetría | Baseline | Q2 2026 |
| 2 | Forensic Rotation | $62/mes | Q2-Q3 |
| 3 | Reputation Cache | $15-30/mes | Q3 |
| 4 | Gossip Backpressure | $25-50/mes | Q3 |
| 5 | Parallel Validation | $20-40/mes | Q4 |
| 6 | Early Termination | $30-60/mes | Q4 |
| **TOTAL** | **6 optimizaciones** | **$152-242/mes** | **By EOY 2026** |

**Impacto esperado:**
- Reducción de costos: 70-80%
- Performance: +3-5x más rápido
- Escalabilidad: Soporta 1000+ nodos

---

## Métricas de Éxito

- ✅ Forensic trail: <100MB después de 12 meses (vs. 870MB actual)
- ✅ Validación: <1 segundo por elección (vs. 5+ actual)
- ✅ Gossip latencia: <300ms 95th percentile (vs. 600ms actual)
- ✅ Costo por nodo: <$1/mes (vs. $4-5 actual)

---

## Dependencias

- Redis 6.0+
- Python 3.11+ (asyncio)
- PostgreSQL 13+ (forensic archive)
- Terraform/CloudFormation (infrastructure-as-code)
