# Swarm mode / Modo enjambre

**Not yet production. / Todavía no es producción.**

Nothing in this repository joins a network. The functions below are pure: the same input gives the same output on every machine. There is no central server in the design.

Nada en este repositorio se une a una red. Las funciones de abajo son puras: la misma entrada da la misma salida en cada máquina. El diseño no tiene un servidor central.

## Idea

Rain World is a game where each creature follows local rules and the world has no referee. This design borrows only that shape: each node applies the same written rules to the same public files. It is not a game, and it does not copy that game's code.

Rain World es un juego en el que cada criatura sigue reglas locales y el mundo no tiene árbitro. Este diseño toma solo esa forma: cada nodo aplica las mismas reglas escritas a los mismos archivos públicos. No es un juego y no copia el código de ese juego.

Joining a room uses a short code, the way a custom match uses a short code. The code is not a secret password and it is not an account. Anyone with the code and the member list can compute the seating.

Unirse a una sala usa un código corto, como un código de partida personalizada. El código no es una clave y no es una cuenta. Quien tenga el código y la lista de miembros puede calcular los puestos.

```text
  public portal
       |
       +---- node A saves the public JSON, hashes it
       +---- node B saves the same public JSON, hashes it
       |
       k of n equal hashes  -->  the group accepts that hash
```

## What is shared

Only a public electoral snapshot and its hash. Never a name, an address, a key, or a message about a person.

Solo una captura electoral pública y su hash. Nunca un nombre, una dirección, una clave, ni un mensaje sobre una persona.

## Join by code

1. One person picks a room code with `room_code_from_seed` (6 characters, no 0/O or 1/I).
2. Each node is a public id, not a legal name. The list has at most 12 seated ids.
3. Every node calls `assign_roles(members, code)`.
4. If the code is not valid, no seating is produced.
5. Members are sorted. Slot 0 is host, then witnesses, archivists, checkers, reserves. The input order does not matter, so there is no race to be first.

The host does not run a server. The host is the person who showed the code. After that, the host follows the same table as everyone else.

## Roles for 12 seats

| Seat | Role | Job |
|---|---|---|
| 1 | host | Shows the code. Then does the same work as a witness. |
| 2–4 | witness | Saves the public JSON and its hash. |
| 5–6 | archivist | Keeps that public file. |
| 7–10 | checker | Compares the hashes the others publish. |
| 11–12 | reserve | Seated. Publishes a hash only if asked by the same rules. |

A 13th id, after sorting, waits. It is not seated.

Quorum is two thirds of the seated nodes, rounded up. One node needs 1 match. Twelve nodes need 8 matching hashes. `agreed_hash` returns that hash, or nothing if no hash reaches the count.

## Code

`src/vigil/swarm/governance.py`

```bash
python3 scripts/swarm_status.py
```

That command prints this status. It does not open a port and it does not join a room.

## What this is not

- Not a running network.
- Not a login.
- Not a place to send personal data.
- The older HTTP routes in `src/vigil/api/routes/swarm.py` are not this design and are not a way to join.
