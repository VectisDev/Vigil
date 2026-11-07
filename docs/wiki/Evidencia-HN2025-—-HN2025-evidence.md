[Español](#español) · [English](#english)

---

## Español

La ficha única es [`docs/evidence/HN2025.md`](https://github.com/VectisDev/Vigil/blob/main/docs/evidence/HN2025.md). Esta página no añade números.

- **64 JSON** en `tests/fixtures/hnd_2025/`. Son respuestas públicas del Consejo Nacional Electoral de Honduras para la elección del 30 de noviembre de 2025.
- Los nombres de archivo van del 3 al 10 de diciembre de 2025. Se guardaron a mano. No los produjo el capturador automático.
- No tienen `previous_hash`. `verify_chain.py` sale en 1, estado `orphans`, 63 archivos después del primero. No son una cadena.
- La raíz Merkle es `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`. El `.ots` compromete esa raíz. No es custodia durante el conteo.
- El hueco más largo entre nombres de archivo es una diferencia de timestamps. No es una medición de que el portal estuviera caído. No hay registro de intentos.
- 2.346 actas inconsistentes menos en 60 minutos (4 dic 2025, 15:00 a 16:00) son 39,15 por minuto, cerca de 3,9× la heurística de 10 por minuto en `src/auditor/inconsistent_acts.py`. No es un estudio pre-registrado. No es una capacidad humana medida.
- Un cambio de share de cerca de −0,504 puntos es una resta entre dos archivos. No es una prueba con un contraste declarado de antemano.

La historia de git de este repositorio empieza después. No hay calibración con 2013, 2017 ni 2021.

Comprobación: [Verificar — Verify](Verificar-—-Verify).

---

## English

The single card is [`docs/evidence/HN2025.md`](https://github.com/VectisDev/Vigil/blob/main/docs/evidence/HN2025.md). This page adds no numbers.

- **64 JSON files** in `tests/fixtures/hnd_2025/`. They are public responses from Honduras' National Electoral Council for the 30 November 2025 election.
- Filename timestamps run from 3 to 10 December 2025. They were saved by hand. The automated poller did not produce them.
- They have no `previous_hash`. `verify_chain.py` exits 1, status `orphans`, 63 files after the first. They are not a chain.
- The Merkle root is `f17dbfe188d2f1a1b31248a343ae3397984ef2ec6550bd1bcded03d31d2a7780`. The `.ots` file commits to that root. It is not custody during the count.
- The longest gap between filenames is a difference of timestamps. It is not a measurement that the portal was down. There is no fetch log.
- 2,346 fewer inconsistent tally sheets in 60 minutes (4 Dec 2025, 15:00 to 16:00) is 39.15 per minute, about 3.9× the heuristic of 10 per minute in `src/auditor/inconsistent_acts.py`. It is not a pre-registered study. It is not a measured human capacity.
- A share change of about −0.504 points is a subtraction of two stored files. It is not a test with a contrast declared beforehand.

The git history of this repository starts later. There is no calibration on 2013, 2017, or 2021.

Check: [Verificar — Verify](Verificar-—-Verify).
