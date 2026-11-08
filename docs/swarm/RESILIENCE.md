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

## Limit / Límite

Vigil cannot recover data that was never published. If the source never sent a file, no node has it, and no number of forks creates it.

Vigil no puede recuperar datos que nunca se publicaron. Si la fuente nunca envió un archivo, ningún nodo lo tiene, y ningún número de forks lo crea.
