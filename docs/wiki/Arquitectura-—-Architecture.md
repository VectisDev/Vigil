[Español](#español) · [English](#english)

---

## Español

### Flujo de extremo a extremo

1. **Captura.** Descarga los datos que publica la autoridad electoral, con límite de velocidad y variación aleatoria de tiempos.
2. **Encadenamiento.** Cada captura se hashea con SHA-256 y se enlaza a la anterior; varias capturas se resumen en una raíz de Merkle.
3. **Anclaje.** La raíz de Merkle se ancla a Bitcoin con OpenTimestamps, sin costo.
4. **Análisis.** 24 reglas estadísticas y 7 detectores forenses buscan anomalías (ver [Metodología](Metodología-—-Methodology)).
5. **Publicación.** Los resultados y la evidencia se publican en el panel y, opcionalmente, en un repositorio de datos separado.

### Las cuatro garantías (T1–T4)

| | Garantía | Qué protege | Límite |
|---|---|---|---|
| **T1** | Cadena de hashes | Detecta cualquier modificación o reordenamiento de capturas pasadas | No prueba quién capturó ni cuándo |
| **T2** | Consenso entre testigos | Con 3 o más testigos tolera uno comprometido | Necesita al menos 2 testigos activos |
| **T3** | Sello de tiempo externo | Prueba en Bitcoin de que los datos existían en una fecha; no se puede retrodatar | Puede tardar más de 10 minutos en confirmarse |
| **T4** | Federación de testigos | Expone a un testigo manipulado o a una autoridad que entrega datos distintos a cada testigo | Falla si más de la mitad de los testigos están comprometidos |

### Federación sin centro

Cada *fork* es un nodo independiente. Los nodos pueden compartir capturas firmadas mediante un protocolo *gossip*, sin coordinador central. Si un nodo recibe de otro una captura válida y firmada, no vuelve a consultar la fuente: el enjambre completo nunca supera la huella de un único visitante respetuoso del sitio auditado.

### Protocolo ARGOS: defensa en profundidad

| Capa | Función | Amenaza que mitiga |
|---|---|---|
| Atestación distribuida | Confirmación cruzada entre testigos | Un testigo comprometido |
| Cifrado en tránsito | ChaCha20-Poly1305 | Intercepción / MITM |
| Tiempos no deterministas | Variación aleatoria de capturas | Bloqueo selectivo predictivo |
| Autorregeneración | Resincronización desde réplicas | Manipulación del estado local |
| Interruptor de emergencia | Congela la operación ante un ataque activo | Compromiso en tiempo real |

### Pila criptográfica

| Primitiva | Uso |
|---|---|
| SHA-256 encadenado y árbol de Merkle | Integridad de las capturas |
| Ed25519 | Firmas de testigos y del operador |
| Fernet (AES-128-CBC + HMAC-SHA256) y HKDF-SHA256 | Copias de seguridad y checkpoints cifrados |
| OpenTimestamps / Bitcoin | Sello de tiempo externo e inmutable |

### Documentación completa

- [Arquitectura técnica y teoremas T1–T4](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/ARCHITECTURE.md)
- [Especificación del protocolo ARGOS](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/ARGOS-PROTOCOL-ES.md)
- [Teoría del cambio](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/THEORY_OF_CHANGE.md)

---

## English

### End-to-end flow

1. **Capture.** Downloads the data the electoral authority publishes, rate-limited and with randomized timing.
2. **Chaining.** Every capture is hashed with SHA-256 and linked to the previous one; batches are summarized in a Merkle root.
3. **Anchoring.** The Merkle root is anchored to Bitcoin through OpenTimestamps, at no cost.
4. **Analysis.** 24 statistical rules and 7 forensic detectors look for anomalies (see [Methodology](Metodología-—-Methodology)).
5. **Publication.** Results and evidence are published on the panel and, optionally, in a separate data repository.

### The four guarantees (T1–T4)

| | Guarantee | What it protects | Limit |
|---|---|---|---|
| **T1** | Hash chain | Detects any modification or reordering of past captures | Does not prove who captured or when |
| **T2** | Witness consensus | With 3 or more witnesses, tolerates one compromised | Needs at least 2 active witnesses |
| **T3** | External timestamp | Bitcoin proof that the data existed at a given date; cannot be backdated | May take 10+ minutes to confirm |
| **T4** | Witness federation | Exposes a tampered witness, or an authority serving different data to each witness | Fails if more than half the witnesses are compromised |

### Federation without a center

Every fork is an independent node. Nodes can share signed captures over a gossip protocol, with no central coordinator. When a node receives a valid signed capture from a peer, it does not query the source again: the whole swarm never exceeds the footprint of a single polite visitor to the audited site.

### ARGOS protocol: defense in depth

| Layer | Function | Threat mitigated |
|---|---|---|
| Distributed attestation | Cross-confirmation between witnesses | A single compromised witness |
| Transit encryption | ChaCha20-Poly1305 | Interception / MITM |
| Non-deterministic timing | Randomized capture timing | Predictive selective blocking |
| Self-regeneration | Resync from replicas | Local state tampering |
| Kill switch | Freezes operation under active attack | Real-time compromise |

### Cryptographic stack

| Primitive | Use |
|---|---|
| Chained SHA-256 and Merkle tree | Capture integrity |
| Ed25519 | Witness and operator signatures |
| Fernet (AES-128-CBC + HMAC-SHA256) and HKDF-SHA256 | Encrypted backups and checkpoints |
| OpenTimestamps / Bitcoin | External, immutable timestamp |

### Full documentation

- [Technical architecture and theorems T1–T4](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/ARCHITECTURE.md)
- [ARGOS protocol specification](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/ARGOS-PROTOCOL-ES.md)
- [Theory of change](https://github.com/VectisDev/Vigil/blob/main/docs/architecture/THEORY_OF_CHANGE.md)
