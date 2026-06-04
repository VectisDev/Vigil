# Dev Diary - 202601 - ArbitrumAnchoring - 01

**Fecha aproximada / Approximate date:** 19-ene-2026 / January 19, 2026  
**Fase / Phase:** Anclaje en Arbitrum One / Arbitrum One anchoring  
**Version interna / Internal version:** v0.0.41  
**Rama / Branch:** main (dev-6)  
**Autor / Author:** userf8a2c4

**Resumen de avances / Summary of progress:**
- Implemente anclaje de hashes via Merkle root en Arbitrum One.  
  Implemented hash anchoring via Merkle root on Arbitrum One.
- Cree el contrato `CentinelAnchor.sol` y el modulo `arbitrum_anchor.py`.  
  Created `CentinelAnchor.sol` contract and `arbitrum_anchor.py` module.
- Centralice la configuracion en `config/config.yaml` e integre batching en el loop principal.  
  Centralized config in `config/config.yaml` and integrated batching in the main loop.

---
# Dev Diary - v0.0.41

## [ES] Anclaje de hashes en Arbitrum One

**Fecha:** 19-ene-2026  
**Autor:** userf8a2c4  
**Version:** v0.0.41

### El problema que vi

Venia usando Polygon testnet para anclar hashes, pero necesitaba algo mas robusto para produccion. Queria que los hashes electorales fueran literalmente inmortales -- que quedaran grabados en una cadena con la seguridad de Ethereum pero sin pagar costos prohibitivos. Despues de evaluar opciones, decidi ir con Arbitrum One como L2.

### Lo que hice

Escribi un contrato nuevo, `CentinelAnchor.sol`, disenado especificamente para recibir Merkle roots. La idea es que en lugar de anclar cada hash individual (lo cual seria carisimo), agrupo los hashes en batches cada 15 minutos, calculo el Merkle root, y anclo solo esa raiz. Cualquiera puede verificar que un hash especifico forma parte del batch reconstruyendo el arbol.

Cree el modulo `arbitrum_anchor.py` en `src/anchor/` para manejar toda la interaccion con el contrato. Centralice la configuracion de Arbitrum en una seccion dedicada dentro de `config/config.yaml` para que todo quedara en un solo lugar.

Finalmente, integre el batching directamente en el loop principal del sistema. Cada 15 minutos, los hashes acumulados se anclan automaticamente.

### Impacto

Los hashes ahora son inmutables e inmortales en Ethereum L2 por un costo estimado menor a $10/mes. Eso era exactamente lo que buscaba: prueba criptografica permanente a un costo que el proyecto puede sostener.

### Proximos pasos

Necesito agregar monitoreo de transacciones para detectar fallos de anclaje, implementar verificacion publica en el frontend, y optimizar el uso de gas donde sea posible.

---

## [EN] Hash Anchoring on Arbitrum One

**Date:** January 19, 2026  
**Author:** userf8a2c4  
**Version:** v0.0.41

### The problem I saw

I had been using Polygon testnet for hash anchoring, but I needed something more robust for production. I wanted the electoral hashes to be literally immortal -- recorded on a chain with Ethereum's security but without prohibitive costs. After evaluating options, I decided to go with Arbitrum One as my L2.

### What I did

I wrote a new contract, `CentinelAnchor.sol`, designed specifically to receive Merkle roots. The idea is that instead of anchoring each individual hash (which would be extremely expensive), I group hashes into batches every 15 minutes, compute the Merkle root, and anchor only that root. Anyone can verify that a specific hash is part of the batch by reconstructing the tree.

I created the `arbitrum_anchor.py` module in `src/anchor/` to handle all the interaction with the contract. I centralized the Arbitrum configuration in a dedicated section within `config/config.yaml` so everything lives in one place.

Finally, I integrated the batching directly into the system's main loop. Every 15 minutes, accumulated hashes are anchored automatically.

### Impact

Hashes are now immutable and immortal on Ethereum L2 at an estimated cost of less than $10/month. That was exactly what I was looking for: permanent cryptographic proof at a cost the project can sustain.

### Next steps

I need to add transaction monitoring to detect anchoring failures, implement public verification on the frontend, and optimize gas usage where possible.
