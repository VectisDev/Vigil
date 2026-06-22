# Dev Diary - 202512 - TransparencyFoundation - 01

**Fecha aproximada / Approximate date:** Diciembre 2025 (estimada) / December 2025 (estimated)  
**Fase / Phase:** Transparencia base e infraestructura de verificacion / Transparency foundations & verification infrastructure  
**Version interna / Internal version:** v0.0.3 (dev-v3)  
**Rama / Branch:** dev-v3  
**Autor / Author:** userf8a2c4

**Resumen de avances / Summary of progress:**
- Publique hashes y CIDs en blockchain; distribui snapshots via IPFS.  
  Published hashes/CIDs on blockchain; distributed snapshots via IPFS.
- Cree una API publica para auditoria externa (FastAPI).  
  Built a public API for external audits (FastAPI).
- Agregue visualizaciones avanzadas y normalice alertas para reportes tecnicos.  
  Added advanced visualizations and normalized alerts for technical reports.
- Persisti metadatos on-chain e IPFS junto a cada snapshot.  
  Persisted on-chain/IPFS metadata alongside each snapshot.

---
# Version 0.0.3 - Dev-v3

## Contexto / Context

Esta version marca el momento en que decidi que la transparencia tenia que ser una pieza central del sistema, no un extra. Llevaba semanas construyendo la logica de scraping y analisis, pero me di cuenta de que sin una forma verificable de demostrar que los datos no habian sido manipulados, todo el esfuerzo perdia credibilidad. Asi que me enfoque en tres pilares: blockchain, IPFS y una API publica.

This version marks the moment I decided that transparency had to be a core piece of the system, not an afterthought. I had been building scraping and analysis logic for weeks, but I realized that without a verifiable way to prove the data hadn't been tampered with, all that effort lost credibility. So I focused on three pillars: blockchain, IPFS, and a public API.

## Lo que construi / What I built

Implemente la publicacion de hashes y CIDs en blockchain usando la testnet de Polygon. La idea era simple: cada snapshot genera un hash, ese hash se ancla on-chain, y cualquiera puede verificar que los datos no cambiaron despues del hecho. Tambien agregue soporte IPFS para que los snapshots se distribuyeran de forma descentralizada -- si alguien quiere verificar un snapshot historico, no depende solo de mi servidor.

La otra pieza grande fue la API publica con FastAPI. Cree endpoints para consultar snapshots, alertas y verificacion. Queria que cualquier auditor externo pudiera conectarse y validar datos sin necesidad de acceso interno al sistema.

I implemented hash and CID publishing on blockchain using the Polygon testnet. The idea was simple: each snapshot generates a hash, that hash gets anchored on-chain, and anyone can verify the data wasn't altered after the fact. I also added IPFS support so snapshots could be distributed in a decentralized way -- if someone wants to verify a historical snapshot, they don't depend solely on my server.

The other big piece was the public API with FastAPI. I created endpoints for querying snapshots, alerts, and verification. I wanted any external auditor to be able to connect and validate data without needing internal access to the system.

## Mejoras que hice / Improvements I made

Persisti los metadatos on-chain e IPFS junto a cada snapshot en SQLite, almacenando `tx_hash`, `ipfs_cid` e `ipfs_tx_hash`. Esto me permite rastrear exactamente donde quedo anclado cada dato.

Tambien normalice las alertas para que tuvieran descripciones claras y consistentes -- antes eran bastante crypticas y dificiles de usar en reportes. Y agregue visualizaciones avanzadas (Benford, outliers, mapa) a los reportes tecnicos, porque me parecia importante que los datos no solo fueran verificables sino tambien comprensibles visualmente.

I persisted the on-chain and IPFS metadata alongside each snapshot in SQLite, storing `tx_hash`, `ipfs_cid`, and `ipfs_tx_hash`. This lets me trace exactly where each piece of data was anchored.

I also normalized the alerts so they had clear, consistent descriptions -- before they were quite cryptic and hard to use in reports. And I added advanced visualizations (Benford, outliers, map) to the technical reports, because I felt it was important that the data be not only verifiable but also visually understandable.

## Notas tecnicas / Technical Notes

- IPFS se activa con `IPFS_ENABLED=true` y `IPFS_API_URL` opcional.
- La publicacion en blockchain es opt-in via `config.yaml`.
- SQLite almacena `tx_hash`, `ipfs_cid` e `ipfs_tx_hash` por snapshot.

- IPFS is enabled with `IPFS_ENABLED=true` and optional `IPFS_API_URL`.
- Blockchain publishing is opt-in via `config.yaml`.
- SQLite stores `tx_hash`, `ipfs_cid`, and `ipfs_tx_hash` per snapshot.
