# Acceso al Panel de Administración

> Este archivo documenta el sistema de acceso. **No contiene seeds ni contraseñas.**

## URL

```
https://vectisdev.github.io/centinel/ops/
```

## Requisitos

- Un **Seed de acceso** de la serie S1 (S1-A … S1-L).
- El seed lo genera el operador con `make wizard` (o `python scripts/setup_wizard.py`).
- Cada seed tiene 24 caracteres base64url (144 bits de entropía, 18 bytes aleatorios).

## Cómo ingresar

1. Abre la URL del panel.
2. Ingresa tu seed en el campo "Seed de acceso".
3. Presiona **Entrar** o `Enter`.
4. La sesión dura **8 horas** (se cierra al cerrar la pestaña).

## Seguridad

- **No se transmite el seed al servidor.** El hash se computa en el navegador
  con PBKDF2-SHA256 (sal: `centinel-admin-salt-v1`, 600 000 iteraciones).
- El archivo `web/access.json` solo contiene **hashes**, nunca seeds en texto plano.
- Si un seed se compromete, regenera inmediatamente con el workflow o `make wizard`.

## Regenerar accesos

### Desde GitHub Actions (recomendado para GitHub Pages)

1. Ve a **Actions → Regenerate Admin Seeds** en el repositorio.
2. Haz clic en **Run workflow**.
3. Descarga el artifact `centinel-seeds-DESCARGAR-Y-GUARDAR-FUERA-DE-LINEA` (expira en 24h).
4. Guarda los seeds en un gestor de contraseñas offline.

### Desde línea de comandos (modo servidor local)

```bash
make wizard
# En "PASO 7", elige regenerar Seed 1.
# Copia los nuevos seeds en un gestor de contraseñas.
# Commitea web/access.json y haz push.
```

## Seeds perdidos

Si se pierden todos los seeds y no hay acceso al panel:

1. Ejecuta el workflow **Regenerate Admin Seeds** desde GitHub Actions (solo el owner del repo).
2. El workflow genera seeds nuevos, actualiza `web/access.json`, y sube el artifact.
3. Descarga el artifact antes de que expire (24 horas).

Alternativa local:
```bash
FORCE_REGENERATE=true python3 .github/scripts/wizard_seeds.py
# Los nuevos seeds quedan en /tmp/centinel-seeds.txt
git add web/access.json && git commit -m "security: regenerate seeds" && git push
```
