# Threat model — summary / Modelo de amenaza — resumen

One maintainer publishes this repository, under the pseudonym VectisDev.
The longer note in [`docs/security/THREAT-MODEL.md`](security/THREAT-MODEL.md) is a design sketch.
Where it describes a witness federation, or a witness list, as already running, this page is the one that matches the tree. That list is not pre-registered here.

Un solo mantenedor publica este repositorio, con el seudónimo VectisDev.
La nota larga en [`docs/security/THREAT-MODEL.md`](security/THREAT-MODEL.md) es un boceto de diseño.
Si describe una federación de testigos, una lista de testigos ya registrada, o un control como si ya operara, manda esta página.

## What is being watched

The published feed, not a ballot box. Useful failures are: a stored capture no longer matches what was stored, or a portal stops answering during a window when a fetch was actually attempted. The software records those events. It does not decide why they happened and it does not name a responsible party.

Lo observado es el flujo publicado, no una urna. Los fallos útiles son: una captura guardada ya no coincide con lo guardado, o un portal deja de responder en una ventana en la que sí hubo un intento. El software registra esos hechos. No decide la causa y no señala un responsable.

## Controls that exist in this tree

| Threat | What the software does |
|---|---|
| Silent change after a capture | SHA-256 link to the previous capture, when the pipeline is running and writing `previous_hash` |
| Dispute about which bytes were stored | Merkle root, plus an OpenTimestamps proof when one was actually created |
| A report that invents a healthy source | `reachable` stays unknown until a fetch is recorded. Unprobed endpoints stay unknown |
| Load on the authority | Hard ceiling of 480 requests/hour per host |
| A public panel treated as a vault | The Pages site is static and has no login. It collects no visitor data |
| Pressure to soften a result | AGPL-3.0. Thresholds live in `command_center/rules.yaml`. They are not a pre-registered study of the 2025 sample |
| The maintainer disappears | Anyone can fork the repository. There is no second maintainer in the tree |

## Out of scope

- A change made before the authority published the file. The tool keeps what was published.
- What happened at a polling station. The bundled 2025 files are national aggregates.
- Why a number moved. That is for a reader, a court, or the public.
- A second operator. None is configured here.
