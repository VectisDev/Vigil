[Español](#español) · [English](#english)

---

## Español

Las contribuciones son bienvenidas: código, reglas estadísticas, presets de países, traducciones y revisión metodológica.

### Preparar el entorno

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
poetry install          # requiere Python 3.11+ y Poetry
make test               # suite de pruebas
make lint               # flake8 + black
```

### Agregar una regla estadística

1. Crea `src/centinel/core/rules/<nombre>_rule.py` con una función `apply(current_data, previous_data, config)` decorada con `@rule(name=..., severity=..., description=..., config_key=...)`.
2. Añade el módulo a `_RULE_MODULES` en `src/centinel/core/rules_engine.py` para que se registre al iniciar.
3. Define sus umbrales en `config/prod/rules.yaml` bajo el mismo `config_key`.
4. Agrega pruebas en `tests/` y documenta la técnica y sus limitaciones en la [metodología](https://github.com/VectisDev/Vigil/blob/main/docs/research/METHODOLOGY.md).

### Antes de abrir un pull request

- [ ] Las pruebas pasan (`make test`) y el código cumple el estilo (`make lint`).
- [ ] Los cambios están acotados a un solo propósito y los mensajes de commit son claros.
- [ ] No hay secretos ni credenciales en el código.
- [ ] Las funciones públicas tienen docstrings; la documentación de políticas va en español e inglés.

### Reglas de convivencia

Este proyecto sigue un [código de conducta](https://github.com/VectisDev/Vigil/blob/main/CODE_OF_CONDUCT.md). Los fallos de seguridad se reportan en privado, nunca en un *issue* público (ver [Seguridad](Seguridad-—-Security)).

### Mejorar esta wiki

La wiki se publica automáticamente desde [`docs/wiki/`](https://github.com/VectisDev/Vigil/tree/main/docs/wiki). Propón los cambios con un pull request sobre esos archivos; las ediciones directas en la wiki están restringidas.

Guía completa: [CONTRIBUTING.md](https://github.com/VectisDev/Vigil/blob/main/CONTRIBUTING.md)

---

## English

Contributions are welcome: code, statistical rules, country presets, translations and methodological review.

### Set up the environment

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
poetry install          # requires Python 3.11+ and Poetry
make test               # test suite
make lint               # flake8 + black
```

### Add a statistical rule

1. Create `src/centinel/core/rules/<name>_rule.py` with an `apply(current_data, previous_data, config)` function decorated with `@rule(name=..., severity=..., description=..., config_key=...)`.
2. Add the module to `_RULE_MODULES` in `src/centinel/core/rules_engine.py` so it registers at startup.
3. Define its thresholds in `config/prod/rules.yaml` under the same `config_key`.
4. Add tests under `tests/` and document the technique and its limitations in the [methodology](https://github.com/VectisDev/Vigil/blob/main/docs/research/METHODOLOGY.md).

### Before opening a pull request

- [ ] Tests pass (`make test`) and the code meets the style checks (`make lint`).
- [ ] Changes are scoped to one purpose and commit messages are clear.
- [ ] There are no secrets or credentials in the code.
- [ ] Public functions have docstrings; policy documentation is in Spanish and English.

### Community rules

This project follows a [code of conduct](https://github.com/VectisDev/Vigil/blob/main/CODE_OF_CONDUCT.md). Security bugs are reported privately, never in a public issue (see [Security](Seguridad-—-Security)).

### Improving this wiki

The wiki is published automatically from [`docs/wiki/`](https://github.com/VectisDev/Vigil/tree/main/docs/wiki). Propose changes through a pull request on those files; direct wiki edits are restricted.

Full guide: [CONTRIBUTING.md](https://github.com/VectisDev/Vigil/blob/main/CONTRIBUTING.md)
