# CENTINEL — Multi-Platform Resilience Mirroring
# Espejado Multi-Plataforma para Resiliencia

**Audit finding addressed:** Point 4 — GitHub monoculture (single-platform dependency).
**Hallazgo de auditoría:** Punto 4 — Monocultura GitHub (dependencia de plataforma única).

## 1. Purpose / Propósito

CENTINEL operates as a public electoral evidence preservation system.
A system that depends on a single commercial platform (GitHub / Microsoft)
for code, evidence storage, and operation is **vulnerable to:**

CENTINEL opera como sistema de preservación de evidencia electoral pública.
Un sistema que depende de una sola plataforma comercial (GitHub / Microsoft)
para código, almacenamiento de evidencia y operación es **vulnerable a:**

1. Account suspension (coordinated reporting, ToS dispute, MLAT subpoena).
2. Geographic blocking by a hostile government (precedent: Turkey 2016,
   Russia 2024, China since inception).
3. Commercial policy change ("election-related content" restrictions).
4. Platform-wide outage or directional change.

For an internet-freedom-positioned project, this contradiction — depending
on a censorable platform to build censorship-resistant infrastructure — is
unacceptable to grant funders such as the Open Technology Fund.

Para un proyecto posicionado como infraestructura de libertad en internet,
esta contradicción — depender de una plataforma censurable para construir
infraestructura resistente a la censura — es inaceptable para donantes
como Open Technology Fund.

## 2. The mirror network / La red de espejos

CENTINEL maintains continuous mirrors on three independent platforms:

CENTINEL mantiene espejos continuos en tres plataformas independientes:

| Node | Platform | Jurisdiction | Role |
|------|----------|--------------|------|
| 🟢 Primary | GitHub | USA (Microsoft) | Active development; primary issue tracker |
| 🔵 Secondary | Codeberg | Germany (Forgejo) | Full git mirror; failover if primary blocked |
| 🟡 Archival | Internet Archive | USA (501c3 non-profit) | Snapshot bundles; jurisdictionally distinct |

| Nodo | Plataforma | Jurisdicción | Rol |
|------|-----------|--------------|-----|
| 🟢 Primario | GitHub | EE.UU. (Microsoft) | Desarrollo activo; issue tracker principal |
| 🔵 Secundario | Codeberg | Alemania (Forgejo) | Espejo git completo; failover si el primario es bloqueado |
| 🟡 Archival | Internet Archive | EE.UU. (501c3 sin fines de lucro) | Bundles de snapshots; jurisdicción distinta |

### Why these three / Por qué estos tres

- **GitHub** — best developer ergonomics, Actions, Pages, community visibility.
  Mejor ergonomía de desarrollador, Actions, Pages, visibilidad en comunidad.
- **Codeberg** — operated by a German non-profit (Codeberg e.V.); does not
  require corporate accountability to any nation-state advertising regime;
  uses Forgejo (community fork of Gitea) ensuring no single-vendor lock-in.
  Operado por una organización sin fines de lucro alemana (Codeberg e.V.);
  no requiere rendir cuentas corporativas a ningún régimen publicitario
  estatal; usa Forgejo (fork comunitario de Gitea) asegurando que no hay
  lock-in de proveedor único.
- **Internet Archive** — already a court-recognized neutral archive in
  multiple jurisdictions; documented use in election integrity litigation
  globally; specifically designed for tamper-evident preservation.
  Archivo neutral ya reconocido por cortes en múltiples jurisdicciones;
  uso documentado en litigios de integridad electoral a nivel global;
  diseñado específicamente para preservación tamper-evident.

### Why not these / Por qué no estos otros

- **GitLab.com** — Same general jurisdictional exposure as GitHub.
- **Bitbucket** — Atlassian; commercial pressure profile too similar to GitHub.
- **IPFS / Filecoin alone** — Pinning service free tiers are unstable
  (Web3.Storage changed model 2024; Estuary shut down). Acceptable as a
  fourth layer once the project has paid pinning capacity, but not as a
  primary today.
- **Self-hosted Forgejo on academic infrastructure** — Strategic target
  for 2027 (Audit Point #4 Option C) but introduces operational burden
  prematurely.

## 3. Setup procedure / Procedimiento de configuración

### One-time setup per operator / Configuración única por operador

#### A. Create accounts and tokens / Crear cuentas y tokens

1. **Codeberg account** (free):
   - Sign up at https://codeberg.org with a low-attribution email.
   - Create a repository: `VectisDev/centinel` (empty, will be populated
     by the first mirror run).
   - Generate a Personal Access Token: Settings → Applications →
     "Manage Access Tokens" → Generate New Token with scopes:
     `write:repository`, `write:user`.
   - Copy the token (shown only once).

2. **Internet Archive account** (free):
   - Sign up at https://archive.org/account/signup.
   - Retrieve S3 API credentials at https://archive.org/account/s3.php.
   - Copy both `S3 access key` and `S3 secret key`.

#### B. Add secrets to GitHub repository / Añadir secretos al repositorio

In the GitHub repository settings → Secrets and variables → Actions →
"New repository secret", add:

En la configuración del repositorio GitHub → Secrets and variables →
Actions → "New repository secret", añadir:

- `CODEBERG_TOKEN` — the Codeberg personal access token.
- `IA_ACCESS_KEY` — Internet Archive S3 access key.
- `IA_SECRET_KEY` — Internet Archive S3 secret key.

#### C. Deploy the workflow / Desplegar el workflow

Copy `mirror.yml` to `.github/workflows/mirror.yml` in the CENTINEL repo
and push to `main`. The first run will be triggered automatically.

Copiar `mirror.yml` a `.github/workflows/mirror.yml` en el repo CENTINEL
y hacer push a `main`. La primera ejecución se disparará automáticamente.

#### D. Verify / Verificar

After the first successful run:

Después de la primera ejecución exitosa:

- Check `https://codeberg.org/VectisDev/centinel` — should have the full
  repo. Verify the HEAD commit matches GitHub.
  Verificar que tiene el repo completo. Verificar que el HEAD commit
  coincide con GitHub.
- Check `https://archive.org/details/centinel-mirror-<current-month>` —
  should contain a `.bundle` file and its `.manifest.json`.
  Verificar que contiene un archivo `.bundle` y su `.manifest.json`.
- Check `docs/transparency/MIRROR-LOG.md` — should have a new row.
  Verificar que tiene una nueva fila.

## 4. Verifying a mirror in case of GitHub unavailability

If `github.com/VectisDev/centinel` becomes unavailable, anyone can
restore the full repository from a mirror:

Si `github.com/VectisDev/centinel` deja de estar disponible, cualquiera
puede restaurar el repositorio completo desde un espejo:

### From Codeberg / Desde Codeberg

```bash
git clone https://codeberg.org/VectisDev/centinel.git
cd centinel
git log --all --decorate --oneline | head -20  # Verify history.
```

### From Internet Archive / Desde Internet Archive

```bash
# Find the most recent bundle / Encontrar el bundle más reciente:
# https://archive.org/details/centinel-mirror-<YYYY-MM>

# Download both the bundle and its manifest / Descargar ambos:
curl -O https://archive.org/download/centinel-mirror-2026-06/centinel-20260608T120000Z-main-abc123def456.bundle
curl -O https://archive.org/download/centinel-mirror-2026-06/centinel-20260608T120000Z-main-abc123def456.bundle.manifest.json

# Verify the bundle's hash matches the manifest / Verificar hash:
EXPECTED=$(python3 -c 'import json,sys; print(json.load(open("centinel-20260608T120000Z-main-abc123def456.bundle.manifest.json"))["bundle_sha256"])')
ACTUAL=$(sha256sum centinel-20260608T120000Z-main-abc123def456.bundle | cut -d' ' -f1)
[[ "$EXPECTED" == "$ACTUAL" ]] && echo "✓ Bundle integrity verified" || echo "✗ MISMATCH — do not use this bundle"

# Restore from the bundle / Restaurar desde el bundle:
git clone centinel-20260608T120000Z-main-abc123def456.bundle centinel-restored
cd centinel-restored
git log --all --decorate --oneline | head -20
```

## 5. Cost analysis / Análisis de costo

Per the Treasurer agent's zero-cost mandate:

Conforme al mandato de costo cero del agente Treasurer:

| Resource | Tier | CENTINEL usage | Headroom |
|----------|------|----------------|----------|
| GitHub Actions minutes | 2,000/month free | ~30 min/month for mirroring | 98.5% available |
| GitHub storage | 500 MB free packages | ~0 (mirroring is push-only) | 100% available |
| Codeberg | "Fair use" no published quota | <100 MB repo, low push frequency | Well within fair use |
| Internet Archive uploads | Free, rate-limited | ~1 bundle/day max, ~50 MB each | Within published guidelines |

| Recurso | Tier | Uso CENTINEL | Margen |
|---------|------|--------------|--------|
| Minutos GitHub Actions | 2,000/mes gratis | ~30 min/mes para mirror | 98.5% disponible |
| GitHub storage | 500 MB gratis | ~0 (mirror es push-only) | 100% disponible |
| Codeberg | "Uso justo" sin cuota publicada | <100 MB repo, baja frecuencia | Bien dentro del uso justo |
| Subidas Internet Archive | Gratis, rate-limited | ~1 bundle/día máx, ~50 MB c/u | Dentro de guías publicadas |

**Total monthly cost: $0.00. / Costo mensual total: $0.00.**

## 6. Threat model deltas / Cambios al modelo de amenazas

### Threats eliminated / Amenazas eliminadas

| Threat | Pre-mirror | Post-mirror |
|--------|-----------|-------------|
| GitHub account suspension | Project disappears | Mirror remains; can re-bootstrap from Codeberg |
| GitHub geographic block | Project inaccessible to operators in region | Codeberg accessible (different netblocks/AS) |
| GitHub deletes history (force-push attack on repo) | History lost | Internet Archive bundles preserve every snapshot |
| Microsoft compelled to take down repo (MLAT) | Project disappears | Codeberg/IA in different jurisdictions |

### Threats remaining (and accepted) / Amenazas restantes (y aceptadas)

| Threat | Reason for acceptance |
|--------|----------------------|
| All three mirror platforms compelled simultaneously | Would require coordinated action across USA + Germany + Internet Archive's independent legal posture. Probability low; cost of further redundancy (paid VPS) violates Zero-Cost mandate. |
| Codeberg outage during a critical window | GitHub remains primary; IA is read-only archive. Codeberg outage degrades resilience but does not block operations. |
| Internet Archive removes specific items | IA has documented policy of preservation; takedowns rare and noisy. If it happens, the existence of the takedown is itself signal. |

## 7. Future enhancements / Mejoras futuras

These are documented as Audit Point #4 Option B/C — not implemented in
this phase, but planned:

Estas se documentan como Punto #4 Opciones B/C — no implementadas en
esta fase, pero planificadas:

1. **Radicle peer-to-peer mirror** — fully decentralized code hosting;
   adds a fourth, cryptographically-self-sovereign tier.
   Espejo peer-to-peer Radicle — hosting de código totalmente
   descentralizado; añade un cuarto tier criptográficamente soberano.
2. **IPFS pinning for evidence** — separate from code mirroring; would
   target the `centinel-data` evidence repository specifically once
   pinning service stability matures.
   Pinning IPFS para evidencia — separado del mirror de código;
   apuntaría al repo de evidencia `centinel-data` específicamente una
   vez que la estabilidad de los servicios de pinning madure.
3. **Self-hosted Forgejo on UPNFM/UNAH academic infrastructure** —
   strategic partnership target for 2027; converts mirror network from
   commercial-only to commercial + academic + non-profit triad.
   Forgejo autoalojado en infraestructura académica UPNFM/UNAH —
   objetivo estratégico de alianza para 2027.

## 8. References / Referencias

- Codeberg e.V. statutes: https://codeberg.org/Codeberg/org/src/branch/main/CodebergStatutes.md
- Internet Archive Terms of Use: https://archive.org/about/terms.php
- GitHub Free Tier limits: https://docs.github.com/billing/managing-billing-for-github-actions
- Project audit context: `docs/security/AUDIT-2026-06-RED-TEAM.md`
