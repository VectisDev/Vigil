"""Grant and pilot prose may not outrun the evidence card.

El texto de grants y del piloto no puede ir más lejos que la ficha.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _wiki_pages() -> list[str]:
    wiki = ROOT / "docs" / "wiki"
    return sorted(path.relative_to(ROOT).as_posix() for path in wiki.glob("*.md") if path.is_file())


SCANNED = [
    "README.md",
    "docs/VERIFY.md",
    "docs/evidence/HN2025.md",
    "docs/operations/PILOT_REPORT_HN_2025.md",
    "docs/operations/RELEASE.md",
    "docs/grants/OTF_ConceptNote_IFF2026.md",
    "docs/grants/BUDGET_NARRATIVE.md",
    "docs/grants/THEORY_OF_CHANGE.md",
    "docs/grants/ROADMAP.md",
    "docs/grants/REGIONAL-NARRATIVE.md",
    "docs/wiki/Piloto-Honduras-2025-—-Honduras-2025-pilot.md",
    "docs/wiki/Observadores-—-Observers.md",
    "docs/international_observers/OBSERVER_GUIDE.md",
    "docs/mathematics/inconsistent-acts.md",
    "docs/research/ARXIV_SUBMISSION.md",
    "web/index.html",
    "web/status/index.html",
    "docs/grants/OTF_CONCEPT_NOTE_FINAL.md",
    "docs/grants/OTF_CONCEPT_NOTE_FINAL.es.md",
    ".github/SECURITY.md",
    "docs/security/SECURITY-POLICY.md",
    "docs/compliance/SECURITY_POLICY.md",
    "docs/THREAT_MODEL.md",
    "docs/legal/GOVERNANCE.md",
    "docs/START.md",
    "docs/operations/SWARM.md",
    "docs/swarm/README.md",
    "docs/swarm/RESILIENCE.md",
    "docs/README.md",
]
SCANNED.extend(_wiki_pages())

# These pages are where a gap was being narrated as a portal outage.
OUTAGE_CLAIM_FILES = {
    "docs/evidence/HN2025.md",
    "docs/operations/PILOT_REPORT_HN_2025.md",
    "docs/wiki/Piloto-Honduras-2025-—-Honduras-2025-pilot.md",
    "docs/grants/OTF_ConceptNote_IFF2026.md",
    "web/index.html",
    "web/status/index.html",
}

PHYSICAL = [
    re.compile(r"físicamente", re.IGNORECASE),
    re.compile(r"fisicamente", re.IGNORECASE),
    re.compile(r"umbral físico", re.IGNORECASE),
    re.compile(r"límite físico", re.IGNORECASE),
    re.compile(r"limite fisico", re.IGNORECASE),
    re.compile(r"physically plausible", re.IGNORECASE),
    re.compile(r"physically implausible", re.IGNORECASE),
    re.compile(r"physical limit", re.IGNORECASE),
]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_scanned_pages_do_not_accuse_or_invent_a_physical_limit() -> None:
    problems: list[str] = []
    for rel in SCANNED:
        text = _read(rel)
        if re.search(r"fraude", text, re.IGNORECASE) or re.search(r"\bfraud\b", text, re.IGNORECASE):
            problems.append(f"{rel}: fraude/fraud")
        for pattern in PHYSICAL:
            if pattern.search(text):
                problems.append(f"{rel}: {pattern.pattern}")
        for match in re.finditer(r"3[.,]9\s*[×x]", text):
            window = text[max(0, match.start() - 220) : match.end() + 220]
            if not re.search(r"heur", window, re.IGNORECASE):
                problems.append(f"{rel}: 3.9× without a heuristic nearby")
        for match in re.finditer(r"pre-?regist", text, re.IGNORECASE):
            before = text[max(0, match.start() - 180) : match.start()]
            if not re.search(r"\b(not|no|sin)\b", before, re.IGNORECASE):
                problems.append(f"{rel}: pre-registered claim without a negation just before it")
    assert problems == []


def test_gap_pages_do_not_call_filename_holes_outages() -> None:
    problems: list[str] = []
    banned = re.compile(r"apag[oó]n|blackout", re.IGNORECASE)
    for rel in OUTAGE_CLAIM_FILES:
        text = _read(rel)
        if banned.search(text):
            problems.append(rel)
    assert problems == []


def test_hnd_2025_report_does_not_invent_a_portal_outage() -> None:
    text = _read("web/reports/hnd_2025.html")
    for phrase in (
        "desaparecieron del servidor",
        "69.6%",
        "límite estadístico para escrutinio manual",
        "SIN BLACKOUT",
        "dejó de reportar candidatos",
    ):
        assert phrase not in text, phrase


def test_old_contact_address_does_not_reappear() -> None:
    """The retired mailbox must not come back in a tracked file."""
    retired = "security@" + "vectis.dev"
    current = "vectisdev26@proton.me"
    problems: list[str] = []
    skip = {".git", ".venv", "__pycache__", "node_modules"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip.intersection(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if retired in text:
            problems.append(str(path.relative_to(ROOT)))
    assert problems == []
    assert current in (ROOT / ".github" / "SECURITY.md").read_text(encoding="utf-8")
    for note in (
        "docs/grants/OTF_CONCEPT_NOTE_FINAL.md",
        "docs/grants/OTF_CONCEPT_NOTE_FINAL.es.md",
    ):
        body = _read(note)
        assert current in body
        assert "[OWNER EMAIL]" not in body
        assert "VectisDev" in body


def test_applicant_is_an_individual_and_notes_are_rolling() -> None:
    """No sponsor placeholder, and no dated OTF window, in the tree."""
    sponsor = "[" + "FISCAL SPONSOR]"
    legal = "[" + "OWNER LEGAL NAME]"
    windows = (
        "Dec 1" + "-7",
        "Dec 1" + "–7",
        "December 1" + "-7",
        "December 1" + "–7",
        "1-7 " + "December",
        "1–7 " + "December",
        "1-7 de " + "diciembre",
        "1–7 de " + "diciembre",
        "cannot be " + "paid",
        "no fiscal " + "host",
    )
    problems: list[str] = []
    skip = {".git", ".venv", "__pycache__", "node_modules"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip.intersection(path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(ROOT))
        if sponsor in text or legal in text:
            problems.append(rel)
        for window in windows:
            if window in text:
                problems.append(f"{rel}: {window}")
    assert problems == []
    english = _read("docs/grants/OTF_CONCEPT_NOTE_FINAL.md")
    spanish = _read("docs/grants/OTF_CONCEPT_NOTE_FINAL.es.md")
    assert "rolling basis" in english
    assert "forma continua" in spanish
    assert "apply through a fiscal sponsor" not in english.lower()
    assert "aplicar a través" not in spanish


def test_security_policy_matches_one_maintainer() -> None:
    policy = _read(".github/SECURITY.md")
    current = "vectisdev26@proton.me"
    assert current in policy
    assert "48 hours" not in policy
    assert "7 days" not in policy
    assert "push protection is enabled" not in policy.lower()
    assert "No third-party security audit has been completed" in policy
    wiki = _read("docs/wiki/Seguridad-—-Security.md")
    assert current in wiki
    assert "48 hours" not in wiki
    assert "7 días" not in wiki
    retired_disclosure = "security-low"
    old_policy = _read("docs/security/SECURITY-POLICY.md")
    assert retired_disclosure not in old_policy
    assert current in old_policy


def test_mailmap_does_not_repeat_the_personal_mailbox() -> None:
    text = (ROOT / ".mailmap").read_text(encoding="utf-8").lower()
    # Built in pieces so this test does not reintroduce the mailbox into the tree.
    mailbox = "node" + "77e1@" + "ya" + "hoo.com"
    assert mailbox not in text
    assert "ya" + "hoo.com" not in text


def test_single_budget_total() -> None:
    budget = _read("docs/grants/BUDGET_NARRATIVE.md")
    note = _read("docs/grants/OTF_ConceptNote_IFF2026.md")
    theory = _read("docs/grants/THEORY_OF_CHANGE.md")
    for text, name in ((budget, "budget"), (note, "note"), (theory, "theory")):
        assert "75,000" in text or "75.000" in text, name
        assert "12 meses" in text or "12 months" in text, name
    assert "180,000" not in budget
    assert "180,000" not in _read("docs/grants/REGIONAL-NARRATIVE.md")
    assert "costo cero absoluto" not in budget.lower()
