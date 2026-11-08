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

Each id is the fingerprint of a key the node holds. It is not a legal name. At most 12 ids. A 13th id is an error. That cap is what limits a flood of new keys: a key that is not in the list is not seated, and a new key starts with score 0. The cap does not prove the 12 keys belong to 12 people.

Cada identificador es la huella de una clave que tiene el nodo. No es un nombre legal. Como máximo 12. Un decimotercero es un error. Ese tope limita una avalancha de claves nuevas: una clave que no está en la lista no se sienta, y una clave nueva empieza con puntuación 0. El tope no prueba que las 12 claves sean de 12 personas.

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

Inside one room, each node publishes one file: the source, the time window, the hash of the public snapshot, the public key fingerprint, and a signature. The private key stays on that node. No legal name, no address, no opinion.

Dentro de una sala, cada nodo publica un archivo: la fuente, la ventana de tiempo, el hash de la captura pública, la huella de la clave pública y una firma. La clave privada se queda en ese nodo. Ni nombre legal, ni dirección, ni opinión.

```text
attestations/<room>/<source>/<window>/<key-fingerprint>.json
```

GitHub is the first place those files can live, as ordinary commits in a public repository, so anyone can read the history. GitHub is one company, so it is a single point of failure. The fallback is the same files in a second public git repository, or in a plain directory served over HTTPS. The bytes are the message. The host is not.

GitHub es el primer sitio donde esos archivos pueden vivir, como commits normales en un repositorio público, para que cualquiera lea la historia. GitHub es una sola empresa, así que es un único punto de fallo. La alternativa son los mismos archivos en un segundo repositorio git público, o en un directorio servido por HTTPS. Los bytes son el mensaje. El anfitrión no lo es.

Between rooms, the only shared record is an aggregate: source, window, agreed hash, how many were required, how many were seated, how many matched. No key, no score, no story. Another room uses that to compare hashes. It does not import anyone's score.

Entre salas, el único registro compartido es un agregado: fuente, ventana, hash acordado, cuántos hacían falta, cuántos estaban sentados, cuántos coincidieron. Ni clave, ni puntuación, ni relato. Otra sala lo usa para comparar hashes. No importa la puntuación de nadie.

## Reputation

The score is an integer. A signed hash that matches the room's agreed hash, inside the window, is +8. The same hash after the window is −4. No file is −4. A different hash is −8. Each window of age halves those points toward zero. After four windows the event counts as nothing. The same list of facts, in any order, gives the same score. An empty list is 0.

La puntuación es un entero. Un hash firmado que coincide con el hash acordado de la sala, dentro de la ventana, es +8. El mismo hash fuera de la ventana es −4. Sin archivo es −4. Un hash distinto es −8. Cada ventana de antigüedad reduce esos puntos a la mitad, hacia cero. A las cuatro ventanas el hecho ya no cuenta. La misma lista de hechos, en cualquier orden, da la misma puntuación. Una lista vacía es 0.

The agreed hash is the k-of-n result from the seated keys. A fact is counted only after the signature on that file has been checked. This module does not check signatures and does not talk to GitHub.

El hash acordado es el resultado k-de-n de las claves sentadas. Un hecho se cuenta solo después de comprobar la firma de ese archivo. Este módulo no comprueba firmas y no habla con GitHub.

## Where the ideas come from and what we simplified

Three outside pictures suggested the shape. They are not specifications, and they are not named in the pages a visitor opens.

One picture is a world where each creature follows local rules and there is no referee. What we kept is that every node can recompute the result from the same written rules. What we dropped is any simulation of creatures or territory.

A second picture, from the game Rain World, is creatures passing along how you treated them. What we kept is that behavior changes a number, and that the number falls as time passes. What we dropped is stories, opinions, and passing the number itself from room to room. The files that move are signed hashes. Anyone recomputes the number. Between rooms, only the aggregate counts move.

The other picture is a short code that lets people meet in one room. What we kept is a 6-character label with no ambiguous characters, rejected if mistyped. What we dropped is matchmaking, a lobby, a privileged host, and any use of the code as a secret.

We also dropped separate jobs (who archives, who checks, who waits). Those jobs need extra rules and let one node accept another node's bytes. One job is easier to audit: each id fetches the public file. We dropped a waiting list past 12 seats, because a silent cut can seat different ids on different machines. Join and leave are edits to the member list, not a second protocol.

The older HTTP routes in `src/vigil/api/routes/swarm.py` are not this design and are not a way to join.

## Code

`src/vigil/swarm/governance.py` seats the room. `src/vigil/swarm/reputation.py` scores facts. Neither one opens a connection.

```bash
python3 scripts/swarm_status.py
```

That command prints this status. It does not open a port and it does not join a room.
