<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/brand/banner-oscuro.svg">
    <img alt="VIGIL — Integridad electoral verificable" src="docs/brand/banner-claro.svg" width="100%">
  </picture>
</p>

<p align="center"><strong>Español</strong> · <a href="README.en.md">English</a></p>

<h1 align="center">VIGIL</h1>

<p align="center"><strong>Integridad electoral verificable</strong></p>

<p align="center">
  <a href="https://github.com/VectisDev/Vigil/actions/workflows/ci.yml"><img alt="CI en la rama main" src="https://img.shields.io/badge/CI-main-D7262E?style=flat&labelColor=0A0A0A"></a>
  <a href="LICENSE"><img alt="Licencia AGPL-3.0" src="https://img.shields.io/badge/licencia-AGPL--3.0-0A0A0A?style=flat&labelColor=D7262E"></a>
  <a href="https://zenodo.org/records/20598892"><img alt="Datos 10.5281/zenodo.20598892" src="https://img.shields.io/badge/datos-10.5281%2Fzenodo.20598892-D7262E?style=flat&labelColor=0A0A0A"></a>
  <a href="https://vectisdev.github.io/Vigil/"><img alt="Página del proyecto" src="https://img.shields.io/badge/p%C3%A1gina-en_l%C3%ADnea-0A0A0A?style=flat&labelColor=D7262E"></a>
</p>

## ¿Qué es VIGIL?

VIGIL mira los portales públicos del Consejo Nacional Electoral de Honduras. Guarda una copia de cada publicación y calcula una huella, un hash, de esa copia. Cualquiera puede comprobar después si la copia sigue igual, sin cuenta en el portal y sin pedirnos permiso.

El caso de referencia es el JSON público de la elección general de 2025. La misma forma de captura sirve para otra autoridad que publique un archivo parecido.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/panel-oscuro.png">
    <img alt="Panel de VIGIL de día. Sin un nodo encendido, la página lo dice." src="docs/images/panel-claro.png" width="100%">
  </picture>
</p>

<p align="center"><em>El panel, de día. En modo noche se ve la misma pantalla en oscuro. Si no hay un nodo encendido, la página lo dice y no inventa una captura.</em></p>

## Qué hace

<table>
  <tr>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="docs/images/icono-vigila-oscuro.svg">
        <img alt="" src="docs/images/icono-vigila.svg" width="28" height="28">
      </picture>
      <br><strong>Vigila</strong>
      <br>Mira el portal público y guarda una copia de lo que publicó.
    </td>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="docs/images/icono-sella-oscuro.svg">
        <img alt="" src="docs/images/icono-sella.svg" width="28" height="28">
      </picture>
      <br><strong>Sella</strong>
      <br>Calcula una huella de esa copia. Si cambia después, la huella ya no coincide.
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="docs/images/icono-verifica-oscuro.svg">
        <img alt="" src="docs/images/icono-verifica.svg" width="28" height="28">
      </picture>
      <br><strong>Verifica</strong>
      <br>Cualquiera repite la comprobación en su máquina, sin cuenta y sin red.
    </td>
    <td width="50%" valign="top">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="docs/images/icono-publica-oscuro.svg">
        <img alt="" src="docs/images/icono-publica.svg" width="28" height="28">
      </picture>
      <br><strong>Publica</strong>
      <br>La página y este repositorio muestran la copia y el estado.
    </td>
  </tr>
</table>

## Tres maneras de empezar

### 1. Ver la página

Abre [vectisdev.github.io/Vigil](https://vectisdev.github.io/Vigil/). No hace falta instalar nada.

### 2. Verificar sin conexión

Hace falta Git, Python 3.11 o superior, y `make`. No hace falta instalar el proyecto ni tener red después de clonar.

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
# La muestra de 2025 no está enlazada: el primer paso avisa y sale con 1.
# El segundo comprueba la huella guardada. Los dos van juntos.
make replay-offline
```

Lo que debes ver, y lo que eso no demuestra, está en [docs/VERIFY.md](docs/VERIFY.md).

### 3. Correrlo con Docker

La misma comprobación, dentro de una imagen. No llama al portal.

```bash
docker build -f Dockerfile.demo -t vigil-demo .
docker run --rm vigil-demo
```

`docker-compose.yml` es para quien ya opera un nodo y tiene claves. No es el primer paso.

## Verificable por cualquiera. Sin pedirnos permiso.

La comprobación usa los archivos de este repositorio y Python. No hay una cuenta que pedir, ni un permiso que concedamos. El detalle, con el resultado que corresponde a la muestra de 2025, está en [docs/VERIFY.md](docs/VERIFY.md).

## Documentación

| Quiero… | Lee… |
|---|---|
| Ver la página | [vectisdev.github.io/Vigil](https://vectisdev.github.io/Vigil/) |
| Comprobar la muestra | [docs/VERIFY.md](docs/VERIFY.md) |
| Saber qué vigila y qué no | [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) |
| Instalarlo y operarlo | [docs/guides/QUICKSTART.md](docs/guides/QUICKSTART.md) |
| Leer la evidencia de 2025 | [docs/evidence/HN2025.md](docs/evidence/HN2025.md) |
| Encontrar el resto | [docs/README.md](docs/README.md) |

## Compatibilidad

| | |
|---|---|
| Sistema | Linux, macOS y Windows |
| Python | 3.11 y 3.12, que es lo que prueba la integración continua |
| Docker | La imagen de demostración usa Python 3.11 |
| Página | Un navegador actual |

## Límites honestos

- La muestra de 2025 es posterior al conteo. No es una cadena tomada mientras la elección estaba abierta. El detalle está en [docs/evidence/HN2025.md](docs/evidence/HN2025.md).
- Comprobar esos archivos demuestra qué bytes se guardaron. No dice por qué cambió un número, ni qué pasó en una mesa. El alcance está en [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).
- Si el panel no ha consultado el portal, lo dice. No presenta una fuente como si estuviera bien. Véase [docs/VERIFY.md](docs/VERIFY.md).

## Contribuir · Seguridad · Conducta

- [Contribuir](CONTRIBUTING.md)
- [Seguridad](SECURITY.md). Un fallo de seguridad no va en un issue público.
- [Código de conducta](CODE_OF_CONDUCT.md)

## Licencia y cita

[GNU AGPL-3.0](LICENSE). Si usas este trabajo, cita con [CITATION.cff](CITATION.cff).

El identificador [10.5281/zenodo.20598892](https://zenodo.org/records/20598892) es del conjunto de datos de Honduras 2025, no de este programa.

La autoría pública es el seudónimo VectisDev. No hay una universidad ni un partido detrás de este repositorio.

El proyecto se llamó antes CENTINEL. Algunos módulos y documentos conservan ese nombre.
