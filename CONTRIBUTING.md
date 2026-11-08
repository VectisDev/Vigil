# Contribuir a VIGIL

Hay una sola persona al frente, con el seudónimo VectisDev.
La autoría pública es esa. No hay una universidad ni un partido detrás del repositorio.

## Reportar

Un fallo que no sea de seguridad va en un issue, con el formulario que corresponda.

Incluye:

- qué hiciste, qué esperabas y qué ocurrió
- el sistema, la versión de Python y el comando
- el mensaje de error, sin secretos ni claves

Un fallo de seguridad no va en un issue. Usa el aviso privado de GitHub o vectisdev26@proton.me. Véase [SECURITY.md](SECURITY.md).

## Sugerir

Una idea también va en un issue, con el formulario de idea.

Di para qué serviría y qué no debería hacer. El programa registra lo que un portal publicó. No señala un responsable y no toma partido.

## Código

Hace falta Git y Python 3.11 o 3.12.

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
python -m pip install -r requirements.txt -r requirements/dev.txt
python -m pytest -q
```

Esos son los comandos que usa la integración continua. `poetry install` también vale, porque `pyproject.toml` es la fuente de las dependencias.

La comprobación sin red, la que no instala el proyecto, es `make replay-offline`.

## Pautas de un pull request

- El cambio es un solo tema.
- La integración continua queda en verde. No se debilita, se salta ni se edita una prueba para que pase.
- Cada commit se ve **Verified** en GitHub. Sirve una firma SSH, una firma GPG o la firma de GitHub.
- El mensaje del commit está en español y dice qué cambió.
- No hay secretos, claves ni contraseñas.
- Si moviste una ruta, actualizaste workflows, `web/`, pruebas, docs, el Makefile y Docker en el mismo cambio.
- No se mueve la evidencia: la cadena de hashes, las anclas de OpenTimestamps, ni lo citado en Zenodo. `web/` se queda donde está. `conftest.py` y `sitecustomize.py` no se mueven.

## Estándares

- Anotaciones de tipo en las funciones nuevas.
- Black, longitud de línea 120, y flake8. La integración continua revisa los Python que el cambio toca.
- Una prueba nueva cubre el comportamiento nuevo, el camino feliz y un caso límite.
- Los docstrings son cortos y dicen por qué, no una paráfrasis del código.
- El texto público no afirma más de lo que los comandos y las pruebas pueden comprobar.

## Ayuda

Lee antes [README.md](README.md) y [docs/README.md](docs/README.md).
Si la duda no es de seguridad, abre un issue.
El correo vectisdev26@proton.me es para lo que no debe ser público.

---

# Contributing to VIGIL

One person maintains this repository, under the pseudonym VectisDev.
That is the public authorship. No university and no party stands behind the repository.

## Report

A bug that is not a security bug belongs in an issue, using the matching form.

Include:

- what you did, what you expected, and what happened
- the system, the Python version, and the command
- the error message, with no secrets and no keys

A security bug does not belong in an issue. Use GitHub private vulnerability reporting or vectisdev26@proton.me. See [SECURITY.md](SECURITY.md).

## Suggest

An idea also belongs in an issue, using the idea form.

Say what it would be for, and what it should not do. The program records what a portal published. It does not name a responsible party and it does not take a side.

## Code

You need Git and Python 3.11 or 3.12.

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
python -m pip install -r requirements.txt -r requirements/dev.txt
python -m pytest -q
```

Those are the commands continuous integration runs. `poetry install` also works, because `pyproject.toml` is the source of the dependencies.

The offline check, the one that does not install the project, is `make replay-offline`.

## Pull request rules

- The change is one topic.
- Continuous integration is green. A test is not weakened, skipped, or edited so that it passes.
- Each commit shows as **Verified** on GitHub. An SSH signature, a GPG signature, or GitHub's own signature is enough.
- The commit message is in Spanish and says what changed.
- There are no secrets, keys, or passwords.
- If you moved a path, you updated workflows, `web/`, tests, docs, the Makefile, and Docker in the same change.
- Evidence does not move: the hash chain, the OpenTimestamps anchors, or anything cited on Zenodo. `web/` stays where it is. `conftest.py` and `sitecustomize.py` do not move.

## Standards

- Type annotations on new functions.
- Black, line length 120, and flake8. Continuous integration checks the Python files the change touches.
- A new test covers the new behavior, the happy path, and an edge case.
- Docstrings are short and say why, not a paraphrase of the code.
- Public text does not claim more than the commands and the tests can check.

## Help

Read [README.md](README.md) and [docs/README.md](docs/README.md) first.
If the question is not about security, open an issue.
The address vectisdev26@proton.me is for what should not be public.
