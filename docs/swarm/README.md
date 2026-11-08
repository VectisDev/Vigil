# Swarm mode / Modo enjambre

## Start here

You do not need an account.
Ask for a room code.
Run `python3 scripts/swarm_join.py CODE`.
Green means the copies match. Yellow means not yet. Red means they disagree.
That is the whole step.

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

The room is built to tolerate Byzantine faults: some seated keys can lie, send two hashes, or stay silent, and the others can still avoid confirming a bad hash.

f = floor((n−1)/3). A room confirms a hash only with at least n−f distinct seated keys signing that same hash for the same source and the same window. That number is always at least 2f+1. For 12 keys, f is 3 and the confirming count is 9. Seven would be 2f+1 and is not enough here: two groups of 7 can overlap only on faulty keys, so two different hashes could both look confirmed.

A signature counts once. A key outside the room does not count. A key that signs two different hashes for one source and window counts for neither. A file from another window does not count. The score is not a signature. Nine low scores still need nine signatures. Eight high scores confirm nothing.

One key tolerates zero faults. Its own hash is not a group result.

La sala tolera fallos bizantinos: algunas claves sentadas pueden mentir, enviar dos hashes o callar, y las demás pueden evitar confirmar un hash malo.

f = floor((n−1)/3). Una sala confirma un hash solo con al menos n−f claves sentadas distintas firmando ese mismo hash para la misma fuente y la misma ventana. Ese número siempre es al menos 2f+1. Para 12 claves, f es 3 y hacen falta 9. Siete sería 2f+1 y aquí no basta: dos grupos de 7 pueden coincidir solo en claves fallidas, así que dos hashes distintos podrían parecer confirmados.

Una firma cuenta una vez. Una clave fuera de la sala no cuenta. Una clave que firma dos hashes distintos para una fuente y una ventana no cuenta para ninguno. Un archivo de otra ventana no cuenta. La puntuación no es una firma. Nueve puntuaciones bajas siguen necesitando nueve firmas. Ocho puntuaciones altas no confirman nada.

Una sola clave no tolera fallos. Su propio hash no es un resultado de grupo.

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

The agreed hash is the one `confirm` returns. A fact is counted only after the signature on that file has been checked. The score can keep a key out of the next room. It cannot change the count in this room. This module does not check signatures and does not talk to GitHub.

El hash acordado es el que devuelve `confirm`. Un hecho se cuenta solo después de comprobar la firma de ese archivo. La puntuación puede dejar una clave fuera de la sala siguiente. No puede cambiar el recuento de esta sala. Este módulo no comprueba firmas y no habla con GitHub.

## Who knows whom

Nodes see key fingerprints, not legal names. That is the anonymity the rules can give. It is not network anonymity. A push to GitHub from a personal account can show who uploaded which file. Hiding the person means the commit must not carry their name, or the files must arrive through the fallback directory. This design does not do that hiding. It only refuses to put a legal name in the attestation.

Los nodos ven huellas de claves, no nombres legales. Ese es el anonimato que las reglas pueden dar. No es anonimato de red. Un push a GitHub desde una cuenta personal puede mostrar quién subió cada archivo. Ocultar a la persona exige que el commit no lleve su nombre, o que los archivos lleguen por el directorio alternativo. Este diseño no hace ese ocultamiento. Solo se niega a poner un nombre legal en la atestación.

## Threats and limits

| Threat | What the rules do | What they do not do |
|---|---|---|
| Sybil: many new keys | More than 12 keys are refused. A key not on the list does not vote. A new key starts at score 0. | They do not prove the 12 keys are 12 people. One person can hold several keys, up to the cap. |
| Collusion: up to f keys lie together | f keys cannot reach n−f signatures by themselves. For 12 keys, 3 colluding keys cannot confirm. | f+1 colluding keys are outside the claim. |
| Equivocation: one key signs two hashes | That key is detected and counted for neither hash. | Detection needs both files. A hidden second signature is not visible. |
| Replay: the same file repeated, or an old window reused | A repeat counts once. Another window does not count, because the window is part of what was signed. | This code does not check the signature. A forged file would have to be rejected before this step. |
| GitHub stops or censors | The same files can live in a second public git repository or an HTTPS directory. | Until someone runs that second copy, GitHub is a single point of failure. |
| Score gaming | The score changes who may sit next time. | The score never confirms a hash. |

Not production. No node is talking to another node.

## GitHub, used in public

Every record is a public GitHub object. Nothing in this map is a private message. None of the write-side pieces below are turned on. This is not production.

| Swarm step | GitHub object | What is public |
|---|---|---|
| Signed attestation | A file in a commit, under `attestations/<room>/<source>/<window>/<key>.json` | The hash, the key fingerprint, the signature |
| Dispute, including equivocation | An Issue from [`.github/ISSUE_TEMPLATE/swarm-equivocation.md`](../../.github/ISSUE_TEMPLATE/swarm-equivocation.md) | Both file paths and both hashes. Comments are not votes |
| Quorum check | An Action that runs `confirm` on those files | The log of the run |
| Daily signed log | A Release, one per day, with the log and its signature as assets | The log. Not enabled here, because a Release is a published tag |
| Room | A Discussion whose title is the room code and whose first post is the list of key fingerprints | The code and the keys. Discussions have to be switched on for the repository. This note does not claim they are on |
| Dashboard | GitHub Pages, the files in `web/` | Static HTML. No tracker, no login |

An Action would only call the pure function. It would not be a second way to declare a hash confirmed. Nine files still have to be in the tree.

Una Action solo llamaría a la función pura. No sería otra forma de declarar un hash confirmado. Los nueve archivos tendrían que seguir estando en el árbol.

### Limits of this host

Numbers below are GitHub's published limits as of the [REST rate-limit page](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api). Secondary limits can change without notice.

- Unauthenticated REST calls: 60 per hour per IP.
- A personal token: 5,000 per hour.
- `GITHUB_TOKEN` inside Actions: 1,000 per hour per repository.
- Content-creating calls (issues, commits through the API, and similar): in general no more than 80 per minute and 500 per hour.
- No more than 100 concurrent API calls.

The [API terms](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) say abusive or too-frequent API use can suspend the account. Tokens must not be pooled to dodge a limit. Polling the API is a bad fit. Reading the git history with `git fetch` is the fit.

Twelve files a day is small. One commit per signature, from twelve keys, every few minutes, is not. That pattern can trip the content limits. The design therefore keeps the files few: one attestation per key per window, not a chat.

### Fallback

If GitHub is down, rate-limited, or refuses the account, the same files are the record. They can sit in a second public git repository or in a directory served over HTTPS. Quorum is computed from the files. It is not computed from GitHub being reachable. Until that second copy exists, GitHub is a single point of failure. Issues, Discussions, Actions, and Releases do not exist on the fallback. The signed files do.

Si GitHub cae, aplica un límite, o rechaza la cuenta, los archivos son el registro. Pueden estar en un segundo repositorio git público o en un directorio servido por HTTPS. El quórum se calcula con los archivos. No se calcula porque GitHub responda. Hasta que esa segunda copia exista, GitHub es un único punto de fallo. Issues, Discussions, Actions y Releases no existen en la alternativa. Los archivos firmados sí.

## Where the ideas come from and what we simplified

Three outside pictures suggested the shape. They are not specifications, and they are not named in the pages a visitor opens.

One picture is a world where each creature follows local rules and there is no referee. What we kept is that every node can recompute the result from the same written rules. What we dropped is any simulation of creatures or territory.

A second picture, from the game Rain World, is creatures passing along how you treated them. What we kept is that behavior changes a number, and that the number falls as time passes. What we dropped is stories, opinions, and passing the number itself from room to room. The files that move are signed hashes. Anyone recomputes the number. Between rooms, only the aggregate counts move.

The other picture is a short code that lets people meet in one room. What we kept is a 6-character label with no ambiguous characters, rejected if mistyped. What we dropped is matchmaking, a lobby, a privileged host, and any use of the code as a secret.

We also dropped separate jobs (who archives, who checks, who waits). Those jobs need extra rules and let one node accept another node's bytes. One job is easier to audit: each id fetches the public file. We dropped a waiting list past 12 seats, because a silent cut can seat different ids on different machines. Join and leave are edits to the member list, not a second protocol.

The older HTTP routes in `src/vigil/api/routes/swarm.py` are not this design and are not a way to join.

## Code

`src/vigil/swarm/governance.py` seats the room. `src/vigil/swarm/bft.py` counts signatures. `src/vigil/swarm/reputation.py` scores facts. None of them opens a connection. The Issue template is the dispute form. No Action in this repository opens a swarm room or cuts a daily Release.

```bash
python3 scripts/swarm_status.py
```

That command prints this status. It does not open a port and it does not join a room.
