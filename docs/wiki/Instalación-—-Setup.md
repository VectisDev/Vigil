[Español](#español) · [English](#english)

---

## Español

Cualquier persona puede operar su propia instancia de VIGIL en un portátil, sin servidores ni costo. Necesitas **Python 3.11 o superior** y **Git**.

### 1. Instalar

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make quickstart        # instala dependencias y abre VIGIL en el navegador
```

`make quickstart` equivale a `make install` seguido de `make launch`. La primera vez abre el asistente de configuración; las siguientes, el panel.

### 2. Configurar

```bash
make wizard
```

El asistente se abre en el navegador (por defecto en `http://127.0.0.1:7474`) y te guía para elegir el país, indicar la URL oficial de resultados y generar las claves de acceso del panel.

### 3. Operar

| Comando | Qué hace |
|---|---|
| `make snapshot` | Captura y hashea una instantánea de los datos oficiales |
| `make pipeline` | Ejecuta el pipeline completo una vez (captura, análisis, anclaje) |
| `make start` / `make stop` | Inicia o detiene el pipeline continuo en segundo plano |
| `make status` / `make logs` | Muestra el estado o sigue los registros en vivo |
| `make reproduce-2025-audit` | Reproduce el análisis forense de Honduras 2025 |
| `centinel doctor` | Antes de una elección, comprueba que se cumple la seguridad que promete el modo activo |
| `centinel panel show` | Panel del operador en la terminal |

### Instancia pública con GitHub Actions

Si haces un *fork* del repositorio, los workflows de GitHub Actions pueden capturar y publicar sin un equipo encendido:

1. Haz el fork y, en la pestaña **Actions** del fork, actívalos.
2. En **Settings → Pages**, elige **GitHub Actions** como fuente: el panel se publica en el siguiente push a `main`.
3. Opcional: separa los datos capturados en un repositorio propio; ver [arquitectura de repositorios de datos](https://github.com/VectisDev/Vigil/blob/main/docs/operations/DATA-REPOS.md).

### Países

Honduras (`HN`) está validado de extremo a extremo. Otros 17 países de América Latina tienen la configuración lista y solo requieren la URL oficial de resultados; el formato (JSON o CSV) se detecta solo. Lista completa y cómo agregar países: [Países — Countries](Países-—-Countries).

### Más detalle

- [Runbooks del operador](https://github.com/VectisDev/Vigil/blob/main/docs/operations/OPERATOR-RUNBOOKS.md)
- [Guía del panel en GitHub Pages](https://github.com/VectisDev/Vigil/blob/main/docs/operations/PAGES-GUIDE.md)
- [Límites de velocidad y captura ética](https://github.com/VectisDev/Vigil/blob/main/docs/RATE_LIMITING.md)

---

## English

Anyone can run their own VIGIL instance on a laptop, with no servers and no cost. You need **Python 3.11 or newer** and **Git**.

### 1. Install

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make quickstart        # installs dependencies and opens VIGIL in the browser
```

`make quickstart` is `make install` followed by `make launch`. The first run opens the setup wizard; later runs open the panel.

### 2. Configure

```bash
make wizard
```

The wizard opens in the browser (by default at `http://127.0.0.1:7474`) and guides you through choosing the country, entering the official results URL and generating the panel access keys.

### 3. Operate

| Command | What it does |
|---|---|
| `make snapshot` | Captures and hashes one snapshot of the official data |
| `make pipeline` | Runs the full pipeline once (capture, analysis, anchoring) |
| `make start` / `make stop` | Starts or stops the continuous background pipeline |
| `make status` / `make logs` | Shows status or follows the live logs |
| `make reproduce-2025-audit` | Reproduces the Honduras 2025 forensic analysis |
| `centinel doctor` | Before an election, checks that the security the active mode promises is actually in place |
| `centinel panel show` | Operator panel in the terminal |

### Public instance with GitHub Actions

If you fork the repository, its GitHub Actions workflows can capture and publish without a machine running:

1. Fork it and enable the workflows in the fork's **Actions** tab.
2. In **Settings → Pages**, choose **GitHub Actions** as the source: the panel is published on the next push to `main`.
3. Optional: keep captured data in a separate repository; see [data repository architecture](https://github.com/VectisDev/Vigil/blob/main/docs/operations/DATA-REPOS.md).

### Countries

Honduras (`HN`) is validated end to end. Seventeen other Latin American countries have presets ready and only need the official results URL; the format (JSON or CSV) is detected automatically. Full list and how to add countries: [Países — Countries](Países-—-Countries).

### More detail

- [Operator runbooks](https://github.com/VectisDev/Vigil/blob/main/docs/operations/OPERATOR-RUNBOOKS.md)
- [GitHub Pages panel guide](https://github.com/VectisDev/Vigil/blob/main/docs/operations/PAGES-GUIDE.md)
- [Rate limiting and ethical capture](https://github.com/VectisDev/Vigil/blob/main/docs/RATE_LIMITING.md)
