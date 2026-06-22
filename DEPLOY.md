# Centinel Engine — 5-Minute Demo Deployment

Bilingual: ES / EN.

This guide brings up a local Centinel Engine instance with **only the public
audit endpoints exposed**, then verifies it end-to-end. No secrets, no cloud
storage, no proxy chain required — designed so any auditor (academic,
international, citizen) can independently reproduce a working deployment.

## Prerequisites

- Docker + Docker Compose v2
- `curl` and `python3` (used by the verification script)
- Port `8000` available on localhost
- Approx. 1.5 GB free disk for the image build

## Step-by-step

```bash
# 1. Clone the repository
git clone https://github.com/<owner>/centinel-engine.git
cd centinel-engine

# 2. Launch the demo stack (build + start)
docker compose -f docker-compose.demo.yml up -d --build

# 3. Verify the deployment (waits for readiness, probes /audit/*)
./scripts/verify_deployment.sh

# 4. Explore
#    Swagger UI : http://localhost:8000/docs
#    Health     : http://localhost:8000/audit/health
#    Chain      : http://localhost:8000/audit/chain/verify
#    Timeline   : http://localhost:8000/audit/timeline
```

Expected output from step 3:

```
=== Waiting for http://localhost:8000 to become reachable ===
  [OK]    Server reachable after Ns

=== Probing /audit/health ===
  [OK]    /audit/health status=ok
  [OK]    /audit/health advertises no_auth_required=true

=== Probing /audit/chain/verify ===
  [OK]    /audit/chain/verify valid=true count=N

=== Probing /audit/timeline ===
  [OK]    /audit/timeline reachable — total=N

=== Summary ===
Checks passed: 4
Checks failed: 0

Centinel deployment healthy. Ready for audit verification.
```

## Verifying a remote deployment

The script supports any reachable URL:

```bash
BASE_URL=https://centinel.example.org ./scripts/verify_deployment.sh
```

This lets observers verify production deployments from anywhere without
needing access credentials.

## What you have just verified

| Check | What it confirms |
|-------|------------------|
| `/audit/health` returns `status=ok` and `no_auth_required=true` | Audit subsystem is up and the public-no-auth contract holds |
| `/audit/chain/verify` returns `valid=true` | Every snapshot links cryptographically to the previous one — no tampering |
| `/audit/timeline` returns a `total` count | Chronological index is browsable |

If any check fails, the deployment is not safe to audit. Investigate logs:

```bash
docker compose -f docker-compose.demo.yml logs centinel-demo
```

## Tearing down

```bash
docker compose -f docker-compose.demo.yml down
```

## ESPAÑOL

Esta guía levanta una instancia local con solo los endpoints publicos de
auditoria expuestos, y verifica el sistema de extremo a extremo. Cualquier
auditor (academico, internacional, ciudadano) puede reproducir un despliegue
funcional de forma independiente.

Requisitos: Docker, Docker Compose v2, curl, python3, puerto 8000 libre,
~1.5 GB de espacio para la imagen.

```bash
git clone https://github.com/<owner>/centinel-engine.git
cd centinel-engine
docker compose -f docker-compose.demo.yml up -d --build
./scripts/verify_deployment.sh
```

El script valida `/audit/health`, `/audit/chain/verify` y `/audit/timeline`.
Si los tres pasan, el despliegue es verificable por un tercero independiente.
