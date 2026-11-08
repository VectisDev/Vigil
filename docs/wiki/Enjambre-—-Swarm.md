[Español](#español) · [English](#english)

---

## Español

**Todavía no es producción.** No hay un segundo observador.

La idea es que más de una persona guarde el mismo canal público y compare esas copias. El árbol tiene rutas HTTP en `src/vigil/api/routes/swarm.py` y un módulo en `src/vigil/federation/gossip.py`. Ninguna red de esas está en marcha. Hay un solo mantenedor.

```bash
python3 scripts/swarm_status.py
```

Ese comando imprime el estado. No abre un puerto y no se une a un par. El texto largo está en [`docs/operations/SWARM.md`](https://github.com/VectisDev/Vigil/blob/main/docs/operations/SWARM.md).

---

## English

**Not yet production.** There is no second observer.

The idea is that more than one person saves the same public feed and compares those copies. The tree has HTTP routes in `src/vigil/api/routes/swarm.py` and a module in `src/vigil/federation/gossip.py`. No such network is running. There is one maintainer.

```bash
python3 scripts/swarm_status.py
```

That command prints the status. It does not open a port and it does not join a peer. The long text is [`docs/operations/SWARM.md`](https://github.com/VectisDev/Vigil/blob/main/docs/operations/SWARM.md).
