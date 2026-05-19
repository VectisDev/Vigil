# Centinel se configura solo

**Version:** 1.0 | **Date:** 2026-05-19 | **Status:** Active | **Audience:** Operadores · Desarrolladores

> El sistema detecta qué falta al arrancar y abre un Issue en tu repositorio con exactamente lo que necesita. Normalmente es un solo paso.  
> The system detects what's missing at startup and opens an Issue in your repository with exactly what it needs. Usually it's a single step.

**No necesitas leer esta guía para hacer el setup.** El sistema te dice exactamente qué hacer. Esta guía es para quienes quieren entender qué está pasando.

---

## ¿Qué pasa cuando haces fork?

Al hacer fork de centinel-engine y activar GitHub Actions, el workflow `setup-wizard.yml` corre automáticamente. El wizard detecta el estado del sistema y actúa:

```
Fork + primer push a main
         │
         ▼
  ¿DATA_REPO_TOKEN configurado?
         │
    NO ──┤──── Abre Issue: "Acción requerida: conectar repositorio de datos"
         │     → Instrucciones exactas con links directos
         │     → Issue se cierra solo cuando termines
         │
    SÍ ──┤──── ¿centinel-data existe?
         │
    NO ──┤──── Crea centinel-data automáticamente
         │     → Estructura de directorios
         │     → Workflows (ipfs-pin, auto-release)
         │     → Cierra el Issue de setup (si estaba abierto)
         │
    SÍ ──┘──── Todo listo → no hace nada
```

El wizard corre cada hora (mientras haya un Issue de setup abierto) y en cada push a `main`.

---

## ¿Qué hace el sistema automáticamente?

Una vez configurado, el sistema opera sin intervención:

- **Captura snapshots** del endpoint electoral cada 15–30 minutos
- **Calcula hashes SHA-256** y mantiene la cadena criptográfica
- **Detecta anomalías** con 24 detectores estadísticos
- **Genera diffs** entre capturas consecutivas
- **Publica datos** en centinel-data en cada captura
- **Genera informes PDF** bilingües y los publica en GitHub Pages
- **Crea backups semanales** en GitHub Releases de centinel-data
- **Ancla a IPFS** en cada push (si `PINATA_JWT` configurado)
- **Publica packs de observadores** cuando cambian documentos clave
- **Envía alertas a Telegram** (si `TELEGRAM_BOT_TOKEN` configurado)
- **Se auto-repara** ante fallos de red con backoff exponencial

---

## ¿Y si no quiero centinel-data?

No hagas nada. Los datos se quedan en centinel-engine.

Sin `DATA_REPO_TOKEN`, todos los workflows funcionan normalmente. Los datos se acumulan en `data/`, `hashes/`, `diffs/` dentro de centinel-engine. No hay errores, no hay mensajes molestos, no hay Issues que resolver.

La única diferencia es que los datos no se publican en un repositorio público separado.

---

## El único paso que GitHub no permite automatizar

GitHub no permite que un workflow cree secrets en otro repositorio, ni que use tokens de otro usuario. Por eso el sistema no puede configurar `DATA_REPO_TOKEN` por sí mismo.

**Por qué se necesita un token propio (PAT) y no el `GITHUB_TOKEN` automático:**

`GITHUB_TOKEN` tiene permisos solo dentro del repositorio actual. Para crear y escribir en `centinel-data` (que es un repositorio separado, posiblemente en otra cuenta), el sistema necesita un Personal Access Token con permiso `repo` del propietario de centinel-data.

Este es el único paso manual en todo el setup. El Issue que abre el wizard tiene links directos y pasos exactos — no requiere buscar nada ni tomar decisiones.

---

## IPFS (opcional)

<details>
<summary>Activar anclaje IPFS con Pinata (clic para expandir)</summary>

IPFS añade una capa de resiliencia: los datos quedan accesibles aunque centinel-data sea eliminado de GitHub.

**Setup en 3 minutos:**

1. Crear cuenta gratuita en [pinata.cloud](https://pinata.cloud)
2. En Pinata: API Keys → New Key → Generate → **copiar el JWT**
3. En GitHub: `centinel-data` → Settings → Secrets → New secret:
   - Name: `PINATA_JWT`
   - Value: el JWT copiado

A partir del próximo push a centinel-data, cada actualización queda anclada en IPFS y el CID se registra en `ipfs-manifest.json`.

Para más detalles: [IPFS-RESILIENCE.md](IPFS-RESILIENCE.md)

</details>

---

## Secrets disponibles

| Secret | Repositorio | Función | Requerido |
|--------|-------------|---------|-----------|
| `DATA_REPO_TOKEN` | centinel-engine | Crear y escribir en centinel-data | Opcional |
| `TELEGRAM_BOT_TOKEN` | centinel-engine | Alertas Telegram | Opcional |
| `TELEGRAM_CHAT_ID` | centinel-engine | ID del chat de Telegram | Opcional |
| `PINATA_JWT` | centinel-data | Anclaje IPFS | Opcional |

Ningún secret es obligatorio. El sistema funciona con cero secrets (modo local silencioso).

---

## Referencias / References

- [DATA-REPOS.md](DATA-REPOS.md) — Arquitectura de separación código/datos
- [IPFS-RESILIENCE.md](IPFS-RESILIENCE.md) — Resiliencia IPFS
- [QUICKSTART.md](QUICKSTART.md) — Primeros pasos para operadores
