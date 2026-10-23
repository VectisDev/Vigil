<p align="center">
  <img src="web/assets/logo.svg" alt="VIGIL — Trustless Electoral Integrity" width="700">
</p>

<h1 align="center">VIGIL</h1>

<p align="center">
  <strong>Trustless electoral integrity verification for Latin America</strong><br>
  <em>Verificación confiable de integridad electoral para América Latina</em>
</p>

<p align="center">
  <a href="https://github.com/VectisDev/Vigil/actions/workflows/ci.yml"><img src="https://github.com/VectisDev/Vigil/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="https://github.com/VectisDev/Vigil/actions/workflows/codeql.yml"><img src="https://github.com/VectisDev/Vigil/actions/workflows/codeql.yml/badge.svg?branch=main" alt="CodeQL"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-2b6cb0.svg" alt="License: AGPL-3.0"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.11%2B-2b6cb0.svg" alt="Python 3.11+"></a>
  <a href="https://zenodo.org/records/20598892"><img src="https://img.shields.io/badge/dataset-10.5281%2Fzenodo.20598892-2f855a.svg" alt="Dataset DOI"></a>
</p>

<p align="center">
  <a href="https://github.com/VectisDev/Vigil/wiki">Wiki</a> ·
  <a href="https://vectisdev.github.io/Vigil/">Public panel</a> ·
  <a href="https://github.com/VectisDev/Vigil/wiki/Observadores-—-Observers">Verify the evidence</a> ·
  <a href="https://github.com/VectisDev/Vigil/wiki/Instalación-—-Setup">Get started</a>
</p>

---

Electoral authorities publish results that citizens must accept on trust. **VIGIL removes that required trust.** It captures the results the authority publishes, chains every capture cryptographically, anchors it to Bitcoin, and lets any third party verify — offline and without the project's cooperation — that the data was not altered after publication.

A single operator can audit a national election from a laptop, at zero cost.

> **Neutrality.** VIGIL does not assert fraud. It detects statistical anomalies in public electoral data and provides cryptographic proof of its integrity for independent human evaluation.
>
> **Neutralidad.** VIGIL no afirma fraude. Detecta anomalías estadísticas en datos electorales públicos y aporta prueba criptográfica de su integridad para evaluación humana independiente.

## Key properties

| | |
|---|---|
| **Verifiable** | A SHA-256 hash chain and Merkle roots that anyone can check offline with one dependency-free script |
| **Tamper-evident in time** | Merkle roots anchored to Bitcoin through OpenTimestamps |
| **Analytical** | 24 statistical rules and 7 forensic detectors, every threshold configurable |
| **Independent** | Uses public data only; needs no permission or cooperation from the authority |
| **Resilient** | Optional peer-to-peer federation of witnesses, with no central point to seize |
| **Respectful** | Rate-limited capture; the whole federation behaves like a single polite visitor |
| **Free** | Runs on a laptop or on GitHub's free tier; AGPL-3.0 keeps it open |

## Verify the evidence

```bash
curl -O https://raw.githubusercontent.com/VectisDev/Vigil/main/verify/verify_chain.py
python3 verify_chain.py path/to/snapshots/
```

Only the Python standard library is required. See the [observer guide](https://github.com/VectisDev/Vigil/wiki/Observadores-—-Observers).

## Get started

```bash
git clone https://github.com/VectisDev/Vigil.git
cd Vigil
make quickstart        # install dependencies and open the setup wizard
make pipeline          # run one full capture-analysis-anchoring cycle
```

Requires Python 3.11+. Full instructions, including running a public instance on GitHub Actions: [setup guide](https://github.com/VectisDev/Vigil/wiki/Instalación-—-Setup).

## Honduras 2025 pilot

A **retroactive forensic analysis** of 64 official JSON files published by Honduras' National Electoral Council for the November 30, 2025 election. Among other anomalies, the engine flagged a 13-hour overnight publication blackout and 2,346 inconsistent tally sheets resolved at 39 per minute. It is a demonstration on real data, not a live audit.

```bash
make reproduce-2025-audit
```

Findings, caveats and data: [pilot page](https://github.com/VectisDev/Vigil/wiki/Piloto-Honduras-2025-—-Honduras-2025-pilot) · [dataset on Zenodo](https://zenodo.org/records/20598892).

## Documentation

| Topic | Where |
|---|---|
| Overview and navigation | [Wiki](https://github.com/VectisDev/Vigil/wiki) |
| Architecture, guarantees T1–T4 and cryptography | [Architecture](https://github.com/VectisDev/Vigil/wiki/Arquitectura-—-Architecture) |
| Detection rules and limitations | [Methodology](https://github.com/VectisDev/Vigil/wiki/Metodología-—-Methodology) |
| Supported countries | [Countries](https://github.com/VectisDev/Vigil/wiki/Países-—-Countries) |
| Validation status and roadmap | [Project status](https://github.com/VectisDev/Vigil/wiki/Estado-del-proyecto-—-Project-status) |
| Grant reviewers and funders | [For funders](https://github.com/VectisDev/Vigil/wiki/Para-financiadores-—-For-funders) |
| Legal framework and neutrality | [Legal and neutrality](https://github.com/VectisDev/Vigil/wiki/Legal-y-neutralidad-—-Legal-and-neutrality) |
| Full technical documentation | [`docs/`](docs/) |

## Security

Please report vulnerabilities privately through [Security → Report a vulnerability](https://github.com/VectisDev/Vigil/security/advisories/new). See [SECURITY.md](SECURITY.md).

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## License

[GNU AGPL-3.0](LICENSE). Any derivative work must remain open, so VIGIL cannot be captured, closed or privatized.

---

<p align="center"><em>VIGIL was formerly known as CENTINEL; some code and documents still use that name.</em></p>
