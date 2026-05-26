# Acceso al Panel de Administración

> Este archivo documenta el sistema de acceso. **No contiene seeds ni contraseñas.**

## URL

```
https://vectisdev.github.io/centinel/admin/
```

## Requisitos

- Un **Seed de acceso** de la serie S1 (S1-A … S1-L).
- El seed lo genera el operador con `make wizard` (o `python scripts/setup_wizard.py`).
- Cada seed tiene 24 caracteres alfanuméricos.

## Cómo ingresar

1. Abre la URL del panel.
2. Ingresa tu seed en el campo "Seed de acceso".
3. Presiona **Entrar** o `Enter`.
4. La sesión dura **8 horas** (se cierra al cerrar la pestaña).

## Seguridad

- **No se transmite el seed al servidor.** El hash se computa en el navegador
  con PBKDF2-SHA256 (sal: `centinel-admin-salt-v1`, 600 000 iteraciones).
- El archivo `web/access.json` solo contiene **hashes**, nunca seeds en texto plano.
- Si un seed se compromete, regenera `access.json` con `make wizard`.

## Regenerar accesos

```bash
make wizard
# En "PASO 7", elige regenerar Seed 1.
# Copia los nuevos seeds en un gestor de contraseñas.
# Commitea web/access.json y haz push.
```

## Acceso de emergencia

Si se pierden todos los seeds:

```bash
python scripts/setup_wizard.py
# Responde "sí" en PASO 7 para generar nuevos seeds.
```
