---
Version: 1.0
Date: 2026-05-19
Status: Active
Audience: Operadores / Fork users
---

# Panel de Visualización — Guía

> **ES:** El panel se despliega y mantiene solo. Esta guía es para quienes quieren entender qué ocurre o necesitan configurar opciones avanzadas.
>
> **EN:** The dashboard deploys and maintains itself. This guide is for those who want to understand the process or configure advanced options.

---

## Qué hace el sistema automáticamente / What the system does automatically

Al hacer fork y activar el primer push a `main`, el setup wizard:

1. Detecta si GitHub Pages está habilitado en el repositorio.
2. Si no lo está, intenta activarlo vía GitHub API con el token automático del workflow.
3. Actualiza el `README.md` con el link real al panel (`https://{tu-usuario}.github.io/vigil/`).
4. A partir de ahí, cada push a `main` que modifique `web/**` redespliega el panel automáticamente.

El panel incluye datos de simulación por defecto. Los datos reales se publican cuando el motor corre.

---

## Si el wizard no pudo activar Pages / If the wizard couldn't enable Pages

El wizard abre un Issue en tu repositorio con un link directo. El único paso:

1. Ve a **[Settings → Pages](../../settings/pages)** de tu repositorio
2. En **"Source"**, selecciona: **GitHub Actions**
3. Clic en **Save**

El panel estará disponible en `https://{tu-usuario}.github.io/vigil/` en el siguiente push.

---

## Claves de operaciones / Ops keys

Quien hace el fork genera las claves y las entrega a su equipo. Cada clave tiene 12 caracteres de un alfabeto de 62 (unos 71 bits). El sitio público no pide la clave y no la comprueba en el navegador.

The forker generates the keys and hands them to their team. Each key is 12 characters from a 62-character alphabet (about 71 bits). The public site does not ask for the key and does not check it in the browser.

```bash
python3 scripts/ops_keys.py generate
```

Eso imprime las claves una vez y escribe solo hashes con sal en `config/ops_keys.yml`. Ese archivo se puede commitear. Las claves no.

That prints the keys once and writes only salted hashes to `config/ops_keys.yml`. That file can be committed. The keys cannot.

---

## Dominio personalizado (opcional) / Custom domain (optional)

<details>
<summary>Configurar dominio propio</summary>

1. Ve a **Settings → Pages** de tu repositorio
2. En **"Custom domain"**, escribe tu dominio (ej. `vigil.tudominio.org`)
3. En tu proveedor DNS, añade un registro CNAME: `vigil.tudominio.org → {tu-usuario}.github.io`
4. Activa **"Enforce HTTPS"** una vez que el dominio esté verificado

El wizard actualizará el placeholder `VIGIL_PAGES_URL` en README.md con el dominio personalizado si detecta que está configurado.

</details>

---

## ¿Qué contiene el panel? / What does the dashboard contain?

| Sección | Descripción |
|---------|-------------|
| **Inicio** (`/`) | Hub central — acceso al panel y al sandbox |
| **Panel** (`/panel/`) | Dashboard electoral: KPIs, mapa, análisis de Benford, detectores forenses |
| **Académico** (`/academico/`) | Sandbox con 576 snapshots de simulación para análisis forense |
| **Replay** (`/replay/`) | Reproducción cronológica de capturas |
| **Verificador** (`/verifier/`) | Verificación de integridad de snapshots individuales |
| **Reportes** (`/reports/`) | Reportes HTML generados automáticamente |

Los datos se regeneran en cada push: calibración, series temporales, snapshots.

---

## Referencias / References

- [DATA-REPOS.md](DATA-REPOS.md) — Separación código/datos
- [SETUP-GUIDE.md](SETUP-GUIDE.md) — Setup wizard completo
- [RESILIENCE.md](RESILIENCE.md) — Resiliencia y federación
