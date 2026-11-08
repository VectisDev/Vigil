# OTF Internet Freedom Fund — concept note

Draft for the online form. This file is not a submitted application.

Checked against the Internet Freedom Fund pages on 7 November 2026:

- Concept-note questions: [Appendix I](https://docs.opentech.fund/otf-application-guidebook/appendix-i-concept-note-guide). That page does not publish a word cap for these answers. Word caps on the [proposal guide](https://docs.opentech.fund/otf-application-guidebook/appendix-ii-proposal-guide) apply only if OTF invites a full proposal.
- Award band: [Internet Freedom Fund](https://www.opentech.fund/funds/internet-freedom-fund/). Awards can be 10,000–900,000 USD for up to 24 months. OTF says ideal asks are 50,000–200,000 USD for 6–12 months. This ask is **75,000 USD for 12 months**, inside that band.
- Payments are performance-based, in USD. The contract is signed with the applicant ([fund page](https://www.opentech.fund/funds/internet-freedom-fund/)). OTF funds individuals as well as projects ([forum post, 6 April 2018](https://we.opentech.fund/t/does-otf-support-projects-individuals-or-both/894)). OTF does not fund connectivity, ICT4D, or policy advocacy as such.
- Concept notes are accepted on a rolling basis ([guidebook](https://docs.opentech.fund/otf-application-guidebook/our-funds-and-fellowships/internet-freedom-fund)). This file does not set a submission date.

Category on the form: **Technology Development** (one category, as the form asks). The work is an open-source tool, not a convening, so the start-date question does not apply.

Paste each heading below into the matching field. Paths are files in this repository.

---

## Project title

VIGIL — a checkable copy of a public results feed

## Describe your project in 1–3 sentences.

Our project keeps a copy of machine-readable results that an official portal already publishes, so a reporter can later see whether those bytes still match and whether a fetch was even attempted. The main beneficiaries are reporters and election observers in Central America who can clone a public repository, starting with the Honduras 2025 JSON in this repo. The offline check is `make replay-offline`, documented in `docs/VERIFY.md`.

## What problem will your project address?

An official portal can publish a JSON file and later replace it, or stop answering, and a person who did not save the first response has nothing to compare. That is an information asymmetry. This note does not say who, if anyone, changed a tally.

What this repository actually holds is 64 JSON files saved by hand from Honduras' National Electoral Council after the 30 November 2025 election (`docs/evidence/HN2025.md`, `tests/fixtures/hnd_2025/`). `verify/verify_chain.py` exits 1 on that directory: 63 files have no `previous_hash`. They are not a hash chain. A Merkle root of those bytes is committed and recomputed by `make replay-offline` (`Makefile`, `Dockerfile.demo`). Gaps between filenames are not measured outages, because no fetch log was kept.

The change this grant pays for is narrower: a record that distinguishes "nobody asked" from "we asked and the portal did not answer" (`tests/fixtures/fetch_logs/`, `scripts/export_static_snapshot.py`). Without that distinction, a missing file is easy to narrate as an outage. If the problem is left as it is, the only copy of the feed is whatever the portal shows today.

## If this project is funded, what form will it take?

Technology Development. The output is improvements to an existing AGPL-3.0 program (`LICENSE`, `pyproject.toml`), not a research paper as the main product, not a training course, and not an event. It is not a connectivity project, not ICT4D, and not policy advocacy, which OTF lists as outside its remit.

## Give a brief overview of the activities in this project.

One person maintains the repository, under the name VectisDev (`docs/operations/BUS_FACTOR.md`). A statistical reader is not hired yet (`docs/legal/GOVERNANCE.md`).

**Objective 1.** A stranger can check the saved sample without the maintainer.

- Activity: keep the CI job `replay-offline` and the job `demo-image` required (`.github/workflows/ci.yml`, `Dockerfile.demo`).
- Activity: the maintainer runs the release workflow once (`docs/operations/RELEASE.md`). This repository has not created that tag.
- Who: VectisDev.
- Deliverable: a GitHub release with a source tarball, a CycloneDX SBOM, `SHA256SUMS`, and a keyless signature.
- When: months 1–3.

**Objective 2.** Public text does not outrun the files.

- Activity: keep `docs/evidence/HN2025.md` as the only description of the 2025 sample, and keep `tests/test_claim_guard.py` in CI.
- Who: VectisDev.
- Deliverable: that test stays green for the 12 months.
- When: months 1–12.

**Objective 3.** "Outage" means a failed fetch that was written down.

- Activity: use the existing rule that `reachable` stays unknown until an attempt is recorded (`scripts/export_static_snapshot.py`). Do not relabel the 2025 filename gaps.
- Who: VectisDev.
- Deliverable: a fetch log from the next window in which the tool is actually pointed at a live portal, or a one-page note that no such window occurred. The 2025 sample stays as it is.
- When: months 3–12.

**Objective 4.** An outside reader for the 10-per-minute heuristic, or a stop.

- The number 10 is `DEFAULT_MAX_RESOLUTION_RATE` in `src/auditor/inconsistent_acts.py`. It is not calibrated on another election. Honduras 2013, 2017, and 2021 are not in the tree (`docs/research/HISTORICAL_CALIBRATION.md`). Critical rules are marked `promotion: exploratory` until a fixture outside the 2025 sample exists (`command_center/rules.yaml`, `tests/test_rule_promotion_gate.py`).
- Activity: hire one reader who is not the maintainer, or write that the hire did not happen. They may confirm the negative result or add `tests/fixtures/promotion/<rule>.json`.
- Who: a reviewer not yet contracted, paid from the line below. VectisDev does not grade their own heuristic.
- Deliverable: a short memo in `docs/research/`, or the outside fixture.
- When: months 2–8.

**Objective 5.** Spanish instructions that add no new numbers.

- Activity: a Spanish page whose only command is the one in `docs/VERIFY.md`.
- Who: VectisDev.
- Deliverable: that page.
- When: months 4–9.

## Are there similar projects that exist already? How is your project different or complementary to those projects?

Certificate Transparency (RFC 6962) is the idea that a later reader should not have to trust the publisher's current copy. OpenTimestamps commits a digest to Bitcoin. This project uses that shape on a public JSON feed and adds a fetch log. It does not observe polling stations, and it does not replace an election-observation mission.

The 2025 files show the limit of the idea when the chain was not written at the time: the verifier fails, on purpose (`docs/VERIFY.md`). Collaboration with any mission or newsroom is not agreed. None is claimed.

## How long do you estimate activities will take?

12 months.

## How much funding do you estimate you will need? (In US Dollars)

75,000 USD. This is the only total in the repository (`docs/grants/BUDGET_NARRATIVE.md`). There is no travel and no conference line. The applicant is the individual maintainer. The public identity is VectisDev. The legal name is given only to the funder at contracting and is not stored in this file. No fiscal sponsor is needed. One may be considered later. None is in place. NLnet, if used, pays an individual directly after each milestone and does not require a legal entity ([NLnet FAQ](https://nlnet.nl/core/faq/)).

| Deliverable | USD |
|---|---|
| Outside statistical reader, not yet hired, or a written stop if the hire does not happen. The 2013–2021 series are already recorded as absent. | 22,000 |
| One signed software release (tarball, CycloneDX SBOM, `SHA256SUMS`, keyless signature). The workflow exists; the tag does not. | 15,000 |
| Fetch-log definition of an outage, used on a later live window. The 2025 sample is not reclassified. | 10,000 |
| Spanish page that repeats `docs/VERIFY.md` and adds no numbers | 12,000 |
| Notes on a second public portal's JSON, desk work only | 8,000 |
| Coordination and contingency, 12 months | 8,000 |
| **Total** | **75,000** |

Cloud servers are not in this table. Keeping the git repository up is the maintainer's time, not a second budget (`docs/operations/BUS_FACTOR.md`).

## Who would benefit from this project?

Reporters and election observers who already read a public results feed and can clone a git repository. We have not run a user study, and we do not say the tool benefits everyone. The concrete user today is a person checking the 64 Honduras files with `docs/VERIFY.md`. A later user is whoever points the same fetch log at another public JSON portal.

## Where are your intended users, or audiences located?

Latin America and the Caribbean, in the United Nations M49 regional list that OTF says it is moving to. The first feed is Honduras' public presidential JSON. The maintainer's residence is not stated in this repository.

## What is your name?

VectisDev

The form allows a pseudonym. That is the public identity (`CITATION.cff`). The legal name is disclosed only to the funder at contracting and is not written in this repository.

## What email address should we use to contact you?

vectisdev26@proton.me

That is the address in `SECURITY.md`, `CITATION.cff`, and `pyproject.toml`.

## Why are you, and your team members, the right people to work on this project?

The repository is the evidence, not a résumé. A third party can run `make replay-offline` (`docs/VERIFY.md`). CI on the default branch includes that job and a pinned container image (`.github/workflows/ci.yml`, `Dockerfile.demo`). The merge that brought that image to the default branch is pull request 796; the CI run on that merge succeeded (GitHub Actions run 42423340598).

There is one maintainer and no university partner (`docs/operations/BUS_FACTOR.md`, `docs/legal/GOVERNANCE.md`). The applicant is that individual. OTF can contract with an individual. No fiscal sponsor is needed. One may be considered later. None is in place.

## Proposed start date

Not applicable. OTF asks this only for community convenings, and only for a date at least 90 days after submission. This project is technology development.
