# Swarm mode / Modo enjambre

**Not yet production. / Todavía no es producción.**

Nothing here joins a network. The same member list and the same room code always produce the same seating on every machine. There is no central server.

Nada de esto se une a una red. La misma lista de miembros y el mismo código de sala dan el mismo resultado en cada máquina. No hay un servidor central.

```text
  public portal
       |
       +-- each seated id downloads the public JSON itself
       +-- each id publishes only the hash
       |
       enough equal hashes  -->  the room accepts that hash
```

## What a room is

A room is a label plus a set of public ids. The label is 6 characters. It is not a key and not an account. A typo is rejected, so a wrong label does not produce a seating.

Una sala es una etiqueta más un conjunto de identificadores públicos. La etiqueta tiene 6 caracteres. No es una clave ni una cuenta. Un error de escritura se rechaza, así que una etiqueta mala no produce puestos.

Each id is a name the group chose for a node. It is not a legal name. At most 12 ids. A 13th id is an error. The list is not cut down in silence, because two machines must not quietly seat different people.

Cada identificador es un nombre que el grupo eligió para un nodo. No es un nombre legal. Como máximo 12. Un decimotercero es un error. La lista no se recorta en silencio, porque dos máquinas no deben sentar a personas distintas sin decirlo.

Join is adding an id and computing again. Leave is removing an id and computing again. There is no other membership step.

Unirse es añadir un identificador y calcular de nuevo. Salir es quitarlo y calcular de nuevo. No hay otro paso.

## One job

Every seat does the same work: download the public file yourself, and publish its hash. Nobody accepts bytes they did not download. Sorting the ids makes the seating independent of who spoke first.

Todos los puestos hacen lo mismo: descargar uno mismo el archivo público y publicar su hash. Nadie acepta bytes que no descargó. Ordenar los identificadores hace que el resultado no dependa de quién habló primero.

| Seats | Job |
|---|---|
| 1–12 | Save the public JSON. Publish its hash. |

## Agreement

Quorum is two thirds of the seated ids, rounded up. Twelve ids need 8 equal hashes. One id needs 1, and that result is that id's own hash, not a group finding. `agreed_hash` returns the hash that reaches the count, or nothing.

El quórum es dos tercios de los identificadores sentados, redondeado hacia arriba. Doce necesitan 8 hashes iguales. Uno necesita 1, y ese resultado es el hash de ese identificador, no un hallazgo de grupo.

## What is shared

Only a public electoral snapshot and its hash. Never a name of a person, an address, a key, or a message about a person.

Solo una captura electoral pública y su hash. Nunca el nombre de una persona, una dirección, una clave, ni un mensaje sobre una persona.

## Where the ideas come from and what we simplified

Two outside pictures suggested the shape. They are not specifications, and they are not named in the pages a visitor opens.

One picture is a world where each creature follows local rules and there is no referee. What we kept is that every node can recompute the result from the same written rules. What we dropped is any simulation of creatures, territory, or reputation.

The other picture is a short code that lets people meet in one room. What we kept is a 6-character label with no ambiguous characters, rejected if mistyped. What we dropped is matchmaking, a lobby, a privileged host, and any use of the code as a secret.

We also dropped separate jobs (who archives, who checks, who waits). Those jobs need extra rules and let one node accept another node's bytes. One job is easier to audit: each id fetches the public file. We dropped a waiting list past 12 seats, because a silent cut can seat different ids on different machines. Join and leave are edits to the member list, not a second protocol.

The older HTTP routes in `src/vigil/api/routes/swarm.py` are not this design and are not a way to join.

## Code

`src/vigil/swarm/governance.py`

```bash
python3 scripts/swarm_status.py
```

That command prints this status. It does not open a port and it does not join a room.
