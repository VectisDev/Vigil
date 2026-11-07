# Política de seguridad | Security policy

La política que aplica es [`.github/SECURITY.md`](../../.github/SECURITY.md).
Si este archivo dice otra cosa, gana ese.

The policy that applies is [`.github/SECURITY.md`](../../.github/SECURITY.md).
If this file disagrees, that file wins.

## Cómo reportar | How to report

Un mantenedor, seudónimo VectisDev. No hay equipo de seguridad.

Reportar en privado:

1. [GitHub → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new)
2. vectisdev26@proton.me

No abras un issue público para un fallo de seguridad. No hay otra dirección.
No hay clave de cifrado publicada en el repositorio.

One maintainer, pseudonym VectisDev. There is no security team.

Report in private:

1. [GitHub → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new)
2. vectisdev26@proton.me

Do not open a public issue for a security bug. There is no other address.
No encryption key is published in the repository.

## Plazo | Timing

La bandeja se revisa con la intención de hacerlo en 14 días. No hay guardia.
No hay acuse en 48 horas ni un plazo fijo de corrección.

The inbox is checked with the intention of doing so within 14 days. There is no on-call.
There is no 48-hour acknowledgement and no fixed fix window.

## Versiones | Versions

No hay un tag de release publicado. Las correcciones entran en `main`.
Cuando exista un tag, el alcance es `main` y el tag más reciente.

No release tag is published. Fixes land on `main`.
Once a tag exists, the scope is `main` and the latest tag.

## Secretos | Secrets

No van al git: tokens, claves privadas, contraseñas, ni claves del panel en claro.
Los secretos de Actions viven en la configuración del repositorio.
Cifrar un archivo y commitearlo sigue siendo un secreto en el repositorio.

Tokens, private keys, passwords, and plaintext panel keys do not go into git.
Actions secrets live in the repository settings.
Encrypting a file and committing it is still a secret in the repository.
