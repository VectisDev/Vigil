# Security policy — pointer

The disclosure policy is [`.github/SECURITY.md`](../../.github/SECURITY.md).
This page used to restate controls that the tree does not provide. Those statements are withdrawn.

One person maintains the repository, under the pseudonym VectisDev. There is no security team.

## What is true

| Topic | What the tree shows |
|---|---|
| Disclosure | Private GitHub advisory, or vectisdev26@proton.me. No public issue. No other address. |
| Timing | Inbox checked with the intention of 14 days. No on-call. No 48-hour reply. No fixed fix window. |
| Supported code | `main` only, until a release tag exists. Then `main` and the latest tag. |
| Public site | Static pages. No login. No visitor data. `web/privacy/index.html`. |
| Hash chain | Written when the pipeline stores `previous_hash`. The 2025 sample has none. |
| TLS to a portal | The collector can compare a certificate hash when the operator configured one (`src/vigil/core/connectivity.py`). This page does not say every fetch pins a certificate. |
| Private keys | Not in the repository. |
| Third-party audit | None completed. |
| Push protection | A GitHub setting. Not asserted here. |
| Paid services | Not forbidden. The funding ask, if any, is the table in `docs/grants/BUDGET_NARRATIVE.md`. |

## What this page does not claim

No NIST or ISO certification. No kill-switch as an incident process. No IPFS publish path. No registered observer list. No on-call witness network.
