---
Version: 3.0
Date: 2026-10-23
Status: Active
Audience: Operadores · Desarrolladores / Operators · Developers
---

# Setup — Referencia técnica / Technical reference

> **ES:** Cómo configurar una instancia de VIGIL, en local o como instancia pública con GitHub Actions. Para empezar en minutos, usa la [guía rápida](../guides/QUICKSTART.md).
>
> **EN:** How to configure a VIGIL instance, locally or as a public instance on GitHub Actions. To start in minutes, use the [quickstart](../guides/QUICKSTART.md).

---

## 1. Asistente local / Local wizard

```bash
make wizard            # abre / opens http://127.0.0.1:7474
```

`make wizard` ejecuta `scripts/launch.py`, que arranca la API local y abre el navegador: el asistente en la primera ejecución y el panel en las siguientes. El puerto se cambia con `VIGIL_PORT`.

`make wizard` runs `scripts/launch.py`, which starts the local API and opens the browser: the wizard on first run, the panel afterwards. Change the port with `VIGIL_PORT`.

### Qué hace la configuración inicial / What initial setup does

`POST /api/setup/init` (solo funciona una vez / only works once):

| Paso / Step | Resultado / Result |
|---|---|
| Valida el país / Validates the country | Debe existir en `src/vigil/countries.py` / Must exist in `src/vigil/countries.py` |
| Genera 12 claves de acceso / Generates 12 access keys | Se entregan en un PDF que solo se descarga una vez / Delivered in a PDF downloaded only once |
| Escribe `web/access.json` / Writes `web/access.json` | Solo hashes de las claves, nunca las claves / Key hashes only, never the keys |
| Escribe `.centinel-setup.json` | Marca la instancia como configurada / Marks the instance as configured |
| Actualiza `command_center/config.yaml` | País y dominio de la autoridad / Country and authority domain |

### Operaciones posteriores / Later operations

Estas llamadas exigen una clave de operador válida (cabecera `X-Vigil-Key`, que el panel envía tras iniciar sesión).

These calls require a valid operator key (`X-Vigil-Key` header, sent by the panel after login).

| Endpoint | ES | EN |
|---|---|---|
| `POST /api/setup/discover_endpoints` | Guarda la URL oficial de resultados y descubre los endpoints por división | Saves the official results URL and discovers per-division endpoints |
| `POST /api/setup/change_country` | Cambia el país sin regenerar claves | Changes country without regenerating keys |
| `POST /api/setup/regenerate` | Regenera las 12 claves e invalida las anteriores (pide una clave actual) | Regenerates the 12 keys and invalidates the old ones (requires a current key) |

---

## 2. Instancia pública con GitHub Actions / Public instance on GitHub Actions

1. **Fork** del repositorio / of the repository.
2. **Actions:** en la pestaña Actions del fork, activa los workflows / in the fork's Actions tab, enable the workflows.
3. **Pages:** Settings → Pages → Source: **GitHub Actions**. `pages.yml` publica `web/` en cada push que cambie `web/**` / publishes `web/` on every push that changes `web/**`.
4. **Claves del panel / Panel keys:** ejecuta el asistente local una vez y sube el `web/access.json` resultante; guarda el PDF de claves fuera del repositorio / run the local wizard once and commit the resulting `web/access.json`; keep the key PDF outside the repository.

### Repositorio de datos (opcional) / Data repository (optional)

Sin configuración, los datos quedan en este repositorio. Para publicarlos en un repositorio aparte (`<tu-usuario>/centinel-data`):

Without configuration, data stays in this repository. To publish it to a separate repository (`<your-account>/centinel-data`):

1. Crea el repositorio público `centinel-data` con una rama `main` / Create the public `centinel-data` repository with a `main` branch. Los workflows no lo crean / Workflows do not create it.
2. Crea un token con acceso de escritura solo a ese repositorio: un *fine-grained token* con **Contents: Read and write** / Create a token with write access to that repository only: a fine-grained token with **Contents: Read and write**.
3. Guárdalo como secreto `DATA_REPO_TOKEN` / Save it as the `DATA_REPO_TOKEN` secret (Settings → Secrets and variables → Actions).

Lo usan / Used by: `pipeline.yml`, `audit.yml`, `emergency-publish.yml`, `observer_pack.yml`, `report_publish.yml`, `scheduler.yml`. Ver / See [DATA-REPOS.md](DATA-REPOS.md).

### Otros secretos opcionales / Other optional secrets

Todos son opcionales: si faltan, el paso correspondiente se omite. / All are optional: if missing, the related step is skipped.

| Secreto / Secret | Workflow | Uso / Use |
|---|---|---|
| `CODEBERG_TOKEN` | `mirror.yml` | Espejo en Codeberg; el destino está fijado a `codeberg.org/VectisDev/centinel`, ajústalo en tu fork / Codeberg mirror; the target is fixed to `codeberg.org/VectisDev/centinel`, change it in your fork |
| `IA_ACCESS_KEY`, `IA_SECRET_KEY` | `mirror.yml` | Copia en Internet Archive / Internet Archive copy |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_BUCKET_NAME` | `s3-mirror.yml` | Espejo en S3 / S3 mirror |
| `ENDPOINTS_JSON` | `poller-B.yml` | Endpoints de captura sin publicarlos en el repo / Capture endpoints kept out of the repo |
| `VIGIL_NTFY_TOPIC` | `audit.yml` | Notificaciones por ntfy.sh / ntfy.sh notifications |

---

## 3. Solución de problemas / Troubleshooting

| Síntoma / Symptom | Causa probable / Likely cause | Solución / Fix |
|---|---|---|
| El panel da 404 / Panel returns 404 | Pages no usa GitHub Actions como fuente / Pages source is not GitHub Actions | Settings → Pages → Source: GitHub Actions; luego ejecuta / then run `pages.yml` |
| Pasos de `centinel-data` fallan al clonar / `centinel-data` steps fail to clone | El repositorio no existe o el token no tiene acceso / Repository missing or token lacks access | Créalo y revisa los permisos del token / Create it and check the token's permissions |
| `"DATA_REPO_TOKEN not configured — data stays local"` | Comportamiento esperado sin el secreto / Expected without the secret | Nada que hacer, o configura el secreto / Nothing to do, or set the secret |
| El asistente responde 409 / Wizard returns 409 | La instancia ya está configurada / Instance already configured | Usa `regenerate` o `change_country` desde el panel / Use `regenerate` or `change_country` from the panel |
| Llamadas de configuración responden 401 / Setup calls return 401 | Falta la clave de operador o no es válida / Missing or invalid operator key | Inicia sesión de nuevo en el panel / Log in to the panel again |
