# VIGIL — Guía rápida / Quickstart

> **ES:** Del clon a la primera captura en pocos minutos. Para verificar evidencia sin instalar nada, ve a la [guía de observadores](https://github.com/VectisDev/Vigil/wiki/Observadores-—-Observers).
>
> **EN:** From clone to first capture in a few minutes. To verify evidence without installing anything, see the [observer guide](https://github.com/VectisDev/Vigil/wiki/Observadores-—-Observers).

---

## 1. Instalar / Install

Requiere / Requires: **Python 3.11+**, **Git**.

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make quickstart        # instala dependencias y abre el asistente / installs dependencies and opens the wizard
```

## 2. Configurar / Configure

```bash
make wizard            # asistente en el navegador / browser wizard → http://127.0.0.1:7474
```

El asistente pide el país y genera las claves de acceso del panel; descarga y guarda el PDF de claves en un lugar seguro. Después, indica la URL oficial de resultados desde el panel.

The wizard asks for the country and generates the panel access keys; download the key PDF and store it safely. Then set the official results URL from the panel.

## 3. Operar / Operate

| Comando / Command | ES | EN |
|---|---|---|
| `make snapshot` | Captura y hashea una instantánea | Capture and hash one snapshot |
| `make pipeline` | Ciclo completo una vez: captura, análisis y anclaje | One full cycle: capture, analysis, anchoring |
| `make start` · `make stop` | Pipeline continuo en segundo plano | Continuous background pipeline |
| `make status` · `make logs` | Estado y registros en vivo | Status and live logs |
| `vigil doctor` | Comprueba la postura de seguridad del modo activo | Checks the active mode's security posture |
| `vigil panel show [--verbose]` | Panel del operador en la terminal | Operator panel in the terminal |
| `vigil audit run` | Autoauditoría de integridad | Integrity self-audit |
| `make reproduce-2025-audit` | Reproduce el piloto Honduras 2025 | Reproduces the Honduras 2025 pilot |

## 4. Registros / Logs

- `logs/attack_log.jsonl` — eventos de defensa, solo anexado / append-only defense events
- `hashes/` — capturas encadenadas y metadatos de custodia / chained snapshots and custody metadata

## Siguiente paso / Next step

- [Runbooks del operador / Operator runbooks](../operations/OPERATOR-RUNBOOKS.md)
- [Cómo leer el panel / Reading the panel](../operations/OPERATOR-PANEL.md)
- [Protocolo ARGOS / ARGOS protocol](../architecture/ARGOS-PROTOCOL-ES.md)
- [Configuración en detalle / Setup reference](../operations/SETUP-GUIDE.md)
