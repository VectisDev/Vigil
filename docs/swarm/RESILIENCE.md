# Resilience / Resistencia

**Not yet production. / Todavía no es producción.**

No second node is running. This page is the rule for when one is.

No hay un segundo nodo en marcha. Esta página es la regla para cuando lo haya.

## Start here / Empieza aquí

Every interruption becomes evidence.

Toda interrupción se convierte en evidencia.

## What that means / Qué significa

A node does not smooth over a gap. When it tries to fetch and the answer does not come, it keeps the last bytes it already stored and signs the time of that failed try. When a copy of the record is removed in one place, copies on other nodes are the evidence that it was there.

Un nodo no disimula un hueco. Cuando intenta descargar y la respuesta no llega, conserva los últimos bytes que ya guardó y firma la hora de ese intento fallido. Cuando una copia del registro desaparece en un sitio, las copias en otros nodos son la evidencia de que estuvo ahí.

## More nodes / Más nodos

One repository is easy to close. Many repositories, on many accounts, are not one switch. Each extra independent node is another copy of the signed files. Taking down one of them leaves the others. This is only true for nodes that already exist. A plan to have them is not the same as having them.

Un repositorio es fácil de cerrar. Muchos repositorios, en muchas cuentas, no son un solo interruptor. Cada nodo independiente de más es otra copia de los archivos firmados. Cerrar uno deja a los demás. Esto solo es cierto para los nodos que ya existen. Un plan de tenerlos no es tenerlos.

Nodes in other countries matter for the same reason. A person outside the country of the source can keep a node when accounts and networks inside that country are closed. Those nodes are not running in this repository today.

Los nodos en otros países importan por la misma razón. Una persona fuera del país de la fuente puede mantener un nodo cuando se cierran cuentas y redes dentro de ese país. Esos nodos no están corriendo en este repositorio hoy.

## What nodes sign / Qué firman los nodos

Each node signs its own attestation: the source, the window, the hash of the bytes it stored, and the time it made the attempt. Another node can show the same hash at its own time. Together those files are a cross-check. They are not a single clock and not a single account.

Cada nodo firma su propia atestación: la fuente, la ventana, el hash de los bytes que guardó y la hora en que hizo el intento. Otro nodo puede mostrar el mismo hash a su propia hora. Juntos, esos archivos son una comprobación cruzada. No son un solo reloj ni una sola cuenta.

## When an account or a repository is closed / Cuando se cierra una cuenta o un repositorio

GitHub can suspend an account or a repository. One suspension removes that copy. It does not remove a fork that already lives under another account, and it does not remove a node that already stored the files outside GitHub. The mitigation is many forks across many accounts, plus nodes kept by people in other countries. Until those copies exist, one suspension is enough to remove the only copy.

GitHub puede suspender una cuenta o un repositorio. Una suspensión quita esa copia. No quita un fork que ya vive en otra cuenta, ni un nodo que ya guardó los archivos fuera de GitHub. La mitigación son muchos forks en muchas cuentas, más nodos de personas en otros países. Hasta que esas copias existan, una suspensión basta para quitar la única copia.

## When GitHub or the network is cut / Cuando se corta GitHub o la red

A node inside a blocked network cannot publish. A node outside that network can keep running. If it tries to fetch the source and the source answers, it signs that. If it tries and the source does not answer, it signs the failed attempt and the time. That signed time is the record of the gap this node observed. A node that did not try has nothing to sign. A missing file with no attempt is not, by itself, a measured stop.

Un nodo dentro de una red bloqueada no puede publicar. Un nodo fuera de esa red puede seguir. Si intenta descargar la fuente y la fuente responde, lo firma. Si intenta y la fuente no responde, firma el intento fallido y la hora. Esa hora firmada es el registro del hueco que este nodo observó. Un nodo que no intentó no tiene nada que firmar. Un archivo ausente sin un intento no es, por sí solo, una parada medida.

## When the source stops publishing / Cuando la fuente deja de publicar

The nodes keep the last bytes they successfully stored. The stop time they can sign is the time of the first failed attempt after a successful one. They do not invent an earlier time, and they do not invent bytes that the source never sent.

Los nodos conservan los últimos bytes que guardaron con éxito. La hora de parada que pueden firmar es la hora del primer intento fallido después de uno exitoso. No inventan una hora anterior, ni bytes que la fuente nunca envió.

## Freedom with visible responsibility / Libertad con responsabilidad visible

Vigil does not forbid a faster pace. The default stays respectful: 480 requests per hour, a gap of at least 1 second, and a burst of at most 8. The numbers live in `config/prod/rate_limiter.yaml` in your own copy. There is no account for this.

Going past that default is the user's freedom. It is applied only after a public commit, signed with a key, adds `rate_override.yml` and one of these lines:

`responsibility: I accept full responsibility for the consequences of requests above the respectful pace, including load on the source comparable to a denial of service.`

`responsibility: Acepto toda la responsabilidad por las consecuencias de peticiones por encima del ritmo respetuoso, incluida una carga sobre la fuente comparable a una denegación de servicio.`

The signature is an anonymous key. It is not a legal name. A key that the person has registered with a GitHub account can still show that account on GitHub. This repository does not store a name.

An unsigned file, a comment, or a score does not change the pace. There is no swarm penalty for using the override. The room does not lower anyone's score for this choice.

Vigil no prohíbe un ritmo más rápido. El valor por defecto sigue siendo respetuoso: 480 peticiones por hora, un hueco de al menos 1 segundo y una ráfaga de 8 como máximo. Los números viven en `config/prod/rate_limiter.yaml` en tu propia copia. Esto no tiene cuenta.

Pasar ese valor es libertad de quien lo usa. Se aplica solo después de un commit público, firmado con una clave, que añada `rate_override.yml` y una de las dos líneas. La firma es una clave anónima, no un nombre legal. Una clave registrada en una cuenta de GitHub puede mostrar esa cuenta en GitHub. Este repositorio no guarda un nombre.

Un archivo sin firma, un comentario o una puntuación no cambian el ritmo. No hay una pena del enjambre por usar este cambio. La sala no baja la puntuación de nadie por esta elección.

The commit also names an ops key id. The person who forks generates those keys and hands them to their team. Each key is 12 characters from a 62-character alphabet (about 71 bits), drawn with a CSPRNG. The key is the secret. The id in the commit is a fingerprint of the key, so a faster pace is attributed to that key and not to a legal name. `config/ops_keys.yml` stores a per-key salt and a PBKDF2 hash. The public site does not ask for the key and does not check it in page script. An Action checks that the named id is active; a local command can hash-compare a key that someone presents. Revocation marks an id revoked, which stops later actions and leaves the id on older commits. Rotation writes a new hash that records which id it replaces. No name, email, or other personal data is stored. The room does not penalize the choice.

El commit también nombra el id de una clave de operaciones. Quien hace el fork genera esas claves y las entrega a su equipo. Cada clave tiene 12 caracteres de un alfabeto de 62 (unos 71 bits), sacados de un CSPRNG. La clave es el secreto. El id del commit es una huella de la clave, así que un ritmo más rápido se atribuye a esa clave y no a un nombre legal. `config/ops_keys.yml` guarda una sal por clave y un hash PBKDF2. El sitio público no pide la clave y no la comprueba en el script de la página. Una Action comprueba que el id esté activo; un comando local puede comparar el hash de una clave que alguien presenta. Revocar marca el id como revocado: frena acciones posteriores y deja el id en los commits viejos. Rotar escribe un hash nuevo que dice a qué id reemplaza. No se guarda nombre, correo ni otro dato personal. La sala no penaliza esta elección.

## How a fetch names itself / Cómo se nombra una descarga

The default name on a request is `Vigil/0.1.0 (+https://github.com/VectisDev/Vigil; key:<id>)`. `<id>` is the public key id, or `unset` when this repository has not issued one. It is one string, not a rotation of other names. The ceiling stays 480 requests per hour per host, and the minimum gap in code is 1 second, the same number as `config/prod/rate_limiter.yaml`. Where a `robots.txt` exists and forbids that name, the fetch stops. Hiding the client is not the default. The source path does not use a stealth browser, a proxy list, or Tor. An operator's network privacy comes from running on GitHub Actions (Microsoft addresses), not from disguise.

El nombre por defecto en una petición es `Vigil/0.1.0 (+https://github.com/VectisDev/Vigil; key:<id>)`. `<id>` es el id público de la clave, o `unset` cuando este repositorio no ha emitido una. Es una sola cadena, no una rotación de otros nombres. El techo sigue siendo 480 peticiones por hora y por host, y el hueco mínimo en el código es 1 segundo, el mismo número que `config/prod/rate_limiter.yaml`. Donde existe un `robots.txt` y prohíbe ese nombre, la descarga se detiene. Ocultar al cliente no es el valor por defecto. La ruta hacia la fuente no usa un navegador oculto, una lista de proxies ni Tor. La privacidad de red de quien opera viene de correr en GitHub Actions (direcciones de Microsoft), no de un disfraz.

## Limit / Límite

Vigil cannot recover data that was never published. If the source never sent a file, no node has it, and no number of forks creates it.

Vigil no puede recuperar datos que nunca se publicaron. Si la fuente nunca envió un archivo, ningún nodo lo tiene, y ningún número de forks lo crea.
