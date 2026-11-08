# Swarm mode

**Not yet production.** No second observer is configured. This page is the whole operator guide.

Swarm mode means more than one person saves the same public feed and compares those saves. The repository has HTTP routes for that idea in `src/vigil/api/routes/swarm.py` (`/api/swarm/connect`, `/api/swarm/attest`, `/api/swarm/status`) and a gossip module in `src/vigil/federation/gossip.py`. Nothing in this tree is running that network. There is one maintainer.

```text
  portal (public JSON)
       |            |
       v            v
  this repo      a second person   <-- not configured
       \            /
        compare the two saved copies
```

## The one command

```bash
python3 scripts/swarm_status.py
```

It prints the status and does not open a port, does not call the portal, and does not join a peer. A real join would need a second operator, a reachable URL, and a review of those routes. That work is not done.
