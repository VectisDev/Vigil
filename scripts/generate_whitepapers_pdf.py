#!/usr/bin/env python
"""
Compile Centinel whitepapers to legible PDFs.

Renders the LaTeX source semantically (sections, theorem environments,
math as Unicode, tables, accents, lists) with reportlab. Not a full TeX
engine, but produces a clean, readable academic-style PDF.
"""

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable,
)

PROJECT_ROOT = Path(__file__).parent.parent
DOCS = PROJECT_ROOT / "docs" / "whitepaper"

_DJV = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("Body", f"{_DJV}/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", f"{_DJV}/DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", f"{_DJV}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Mono", f"{_DJV}/DejaVuSansMono.ttf"))
addMapping("Body", 0, 0, "Body")
addMapping("Body", 1, 0, "Body-Bold")
addMapping("Body", 0, 1, "Body-Italic")
addMapping("Body", 1, 1, "Body-Bold")
FONT, FONT_B, FONT_M = "Body", "Body-Bold", "Mono"

# --- LaTeX accent / escape handling -------------------------------------
ACCENTS = {
    r"\'a": "á", r"\'e": "é", r"\'i": "í", r"\'o": "ó", r"\'u": "ú",
    r"\'A": "Á", r"\'E": "É", r"\'I": "Í", r"\'O": "Ó", r"\'U": "Ú",
    r"\'\i": "í", r'\"a': "ä", r'\"o': "ö", r'\"u': "ü", r'\"e': "ë",
    r"\~n": "ñ", r"\~N": "Ñ", r"\~a": "ã", r"\~o": "õ",
    r"\^a": "â", r"\^e": "ê", r"\^o": "ô", r"\`a": "à", r"\`e": "è",
}

MATH = {
    r"\,\Vert\,": " ∥ ", r"\Vert": " ∥ ", r"\concat": " ∥ ",
    r"\Hash": "H", r"\Sign": "Sig", r"\Verify": "Vrf",
    r"\negl": "negl", r"\lambda": "λ", r"\tau": "τ", r"\sigma": "σ",
    r"\mu": "μ", r"\le": "≤", r"\ge": "≥", r"\neq": "≠", r"\wedge": "∧",
    r"\Rightarrow": "⇒", r"\rightarrow": "→", r"\to": "→",
    r"\leftarrow": "←", r"\in": "∈", r"\bot": "⊥", r"\dots": "…",
    r"\ldots": "…", r"\cdot": "·", r"\setminus": "∖", r"\Pr": "Pr",
    r"\times": "×", r"\ge ": "≥ ", r"\langle": "⟨", r"\rangle": "⟩",
    r"\{0,1\}": "{0,1}", r"\{": "{", r"\}": "}", r"\quad": "   ",
    r"\,": " ", r"\;": " ", r"\:": " ", r"\!": "",
    r"\big": "", r"\Big": "", r"\left": "", r"\right": "",
}
GREEK = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ"}


def render_math(expr: str) -> str:
    """LaTeX math -> reportlab mini-HTML with <sub>/<super> tags."""
    expr = expr.strip().replace(r"\,\Vert\,", " ∥ ")
    # \mathcal/\mathsf/\mathtt/\mathrm/\mathbf{X} -> X (keep arg)
    expr = re.sub(r"\\math(?:cal|sf|tt|rm|bf|bb|it)\{([^{}]*)\}",
                  r"\1", expr)
    for k, v in sorted(MATH.items(), key=lambda x: -len(x[0])):
        expr = expr.replace(k, v)
    expr = re.sub(r"\\(alpha|beta|gamma|delta)",
                  lambda m: GREEK[m.group(1)], expr)
    # subscripts / superscripts -> tags (font-independent)
    expr = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", expr)
    expr = re.sub(r"_([A-Za-z0-9])", r"<sub>\1</sub>", expr)
    expr = re.sub(r"\^\{([^{}]*)\}", r"<super>\1</super>", expr)
    expr = re.sub(r"\^([A-Za-z0-9*+\-])", r"<super>\1</super>", expr)
    expr = re.sub(r"\\[A-Za-z]+", lambda m: m.group(0)[1:], expr)
    expr = expr.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r" +", " ", expr).strip()


def deescape(text: str) -> str:
    for k, v in sorted(ACCENTS.items(), key=lambda x: -len(x[0])):
        text = text.replace(k, v)
    text = text.replace(r"\_", "_").replace(r"\#", "#")
    text = text.replace(r"\$", "$").replace(r"\&", "&amp;")
    return text


def inline(text: str) -> str:
    """Convert inline LaTeX markup to reportlab mini-HTML."""
    text = deescape(text)
    # math $...$ and \[...\]
    text = re.sub(r"\\\[(.+?)\\\]", lambda m: "<i>" + render_math(m.group(1)) + "</i>", text, flags=re.S)
    text = re.sub(r"\$([^$]+)\$", lambda m: "<i>" + render_math(m.group(1)) + "</i>", text)
    # nested-brace-safe single-arg commands
    for cmd, (op, cl) in {
        "textbf": ("<b>", "</b>"), "emph": ("<i>", "</i>"),
        "textit": ("<i>", "</i>"), "texttt": ('<font face="Mono">', "</font>"),
        "code": ('<font face="Mono">', "</font>"),
    }.items():
        text = re.sub(r"\\" + cmd + r"\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
                       lambda m, o=op, c=cl: o + m.group(1) + c, text)
    text = re.sub(r"\\url\{([^}]*)\}", r'<font color="blue">\1</font>', text)
    text = re.sub(r"\\cite\{[^}]*\}", "[ref]", text)
    text = re.sub(r"\\ref\{[^}]*\}", "§", text)
    text = re.sub(r"\\eqref\{[^}]*\}", "(eq)", text)
    text = text.replace(r"\S", "§").replace(r"\,", " ").replace(r"\ ", " ")
    text = text.replace(r"\bigskip", "").replace(r"\noindent", "")
    text = text.replace(r"\medskip", "").replace(r"\smallskip", "")
    text = text.replace("~", " ").replace(r"\%", "%").replace(r"\&", "&")
    text = re.sub(r"\\[a-zA-Z]+\*?", "", text)  # drop leftover commands
    text = text.replace("\\ ", " ").replace("\\", "")
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_styles():
    ss = getSampleStyleSheet()
    base = dict(fontName=FONT)
    styles = {
        "title": ParagraphStyle("title", parent=ss["Title"], fontName=FONT_B,
                                 fontSize=19, leading=23, alignment=TA_CENTER,
                                 spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", parent=ss["Normal"], fontName=FONT,
                                    fontSize=11.5, leading=15, alignment=TA_CENTER,
                                    spaceAfter=2,
                                    textColor=colors.HexColor("#333333")),
        "author": ParagraphStyle("author", parent=ss["Normal"], fontName=FONT,
                                  fontSize=9.5, alignment=TA_CENTER, spaceAfter=14,
                                  textColor=colors.HexColor("#555555")),
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontName=FONT_B,
                              fontSize=13.5, leading=17, spaceBefore=15, spaceAfter=6,
                              textColor=colors.HexColor("#1a1a2e")),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName=FONT_B,
                              fontSize=11.5, leading=15, spaceBefore=9, spaceAfter=4,
                              textColor=colors.HexColor("#16213e")),
        "para": ParagraphStyle("para", parent=ss["BodyText"], fontSize=9.5,
                                leading=13.5, alignment=TA_JUSTIFY, spaceAfter=6,
                                **base),
        "thm": ParagraphStyle("thm", parent=ss["BodyText"], fontSize=9.5,
                               leading=13.5, alignment=TA_JUSTIFY, spaceAfter=6,
                               leftIndent=8, backColor=colors.HexColor("#f4f4f8"),
                               borderPadding=6, **base),
        "proof": ParagraphStyle("proof", parent=ss["BodyText"], fontSize=9,
                                 leading=12.5, alignment=TA_JUSTIFY, spaceAfter=6,
                                 leftIndent=8, textColor=colors.HexColor("#333333"),
                                 **base),
        "abstract": ParagraphStyle("abstract", parent=ss["BodyText"], fontSize=9,
                                    leading=12.5, alignment=TA_JUSTIFY, spaceAfter=6,
                                    leftIndent=14, rightIndent=14, **base),
        "runt": ParagraphStyle("runt", parent=ss["BodyText"], fontSize=9.5,
                                leading=13.5, alignment=TA_JUSTIFY, spaceAfter=6,
                                **base),
    }
    return styles


def parse_latex(src: str):
    """Yield (kind, payload) tuples from the LaTeX body."""
    body = src.split(r"\begin{document}")[1].split(r"\end{document}")[0]
    body = re.sub(r"(?<!\\)%.*", "", body)  # strip comments

    # protect environments we care about
    env_pat = re.compile(
        r"\\begin\{(abstract|theorem|lemma|corollary|definition|assumption|remark|proof|itemize|enumerate|table|thebibliography|tabular)\}(\[[^\]]*\])?(.*?)\\end\{\1\}",
        re.S,
    )
    pos = 0
    for m in env_pat.finditer(body):
        if m.start() > pos:
            yield from parse_plain(body[pos:m.start()])
        yield ("env", (m.group(1), m.group(3)))
        pos = m.end()
    if pos < len(body):
        yield from parse_plain(body[pos:])


def parse_plain(chunk: str):
    token = re.compile(
        r"\\(section\*?|subsection\*?|paragraph)\{((?:[^{}]|\{[^{}]*\})*)\}"
        r"|\\maketitle|\\tableofcontents|\\newpage|\\appendix"
        r"|\\(title|author|date)\{((?:[^{}]|\{[^{}]*\})*)\}"
    )
    pos = 0
    buf = []

    def flush():
        text = "".join(buf).strip()
        buf.clear()
        if text:
            for para in re.split(r"\n\s*\n", text):
                p = inline(para)
                if p:
                    yield ("para", p)

    for m in token.finditer(chunk):
        buf.append(chunk[pos:m.start()])
        yield from flush()
        if m.group(1):
            kind = m.group(1).rstrip("*")
            yield (("h1" if kind == "section" else
                    "h2" if kind == "subsection" else "run"),
                   inline(m.group(2)))
        elif m.group(3) == "title":
            yield ("title", m.group(4))
        elif m.group(3) == "author":
            yield ("author", m.group(4))
        pos = m.end()
    buf.append(chunk[pos:])
    yield from flush()


def env_to_flow(name, content, styles):
    flow = []
    label = {
        "theorem": "Theorem", "lemma": "Lemma", "corollary": "Corollary",
        "definition": "Definition", "assumption": "Assumption",
        "remark": "Remark", "proof": "Proof",
    }.get(name)
    if name == "abstract":
        for para in re.split(r"\\bigskip|\n\s*\n", content):
            t = inline(para)
            if t:
                flow.append(Paragraph(t, styles["abstract"]))
        return flow
    if name == "thebibliography":
        flow.append(Paragraph("References", styles["h1"]))
        for item in re.split(r"\\bibitem\{[^}]*\}", content)[1:]:
            t = inline(item)
            if t:
                flow.append(Paragraph("• " + t, styles["para"]))
        return flow
    if name in ("itemize", "enumerate"):
        items = re.split(r"\\item", content)[1:]
        for i, it in enumerate(items, 1):
            t = inline(it)
            if t:
                bullet = "•" if name == "itemize" else f"{i}."
                flow.append(Paragraph(f"{bullet}&nbsp;&nbsp;{t}", styles["para"]))
        return flow
    if name == "tabular":
        return flow  # handled inside 'table'
    if name == "table":
        tm = re.search(r"\\begin\{tabular\}(\{[^}]*\})?(.*?)\\end\{tabular\}",
                        content, re.S)
        cap = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", content, re.S)
        if tm:
            rows = []
            raw = re.sub(r"\\(top|mid|bottom)rule|\\hline", "", tm.group(2))
            for line in raw.split(r"\\"):
                line = line.strip()
                if not line:
                    continue
                cells = [inline(c) for c in line.split("&")]
                rows.append([Paragraph(c, styles["para"]) for c in cells])
            if rows:
                ncol = max(len(r) for r in rows)
                rows = [r + [Paragraph("", styles["para"])] * (ncol - len(r)) for r in rows]
                tbl = Table(rows, hAlign="CENTER")
                tbl.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8f0")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]))
                flow.append(tbl)
        if cap:
            flow.append(Spacer(1, 3))
            flow.append(Paragraph("<i>Table.</i> " + inline(cap.group(1)),
                                   styles["proof"]))
        return flow
    if label:
        title_m = re.match(r"\s*\[((?:[^\[\]]|\[[^\]]*\])*)\]", content)
        head = label
        if title_m:
            head += f" ({inline(title_m.group(1))})"
            content = content[title_m.end():]
        content = re.sub(r"\\label\{[^}]*\}", "", content)
        style = styles["proof"] if name == "proof" else styles["thm"]
        body = inline(content)
        flow.append(Paragraph(f"<b>{head}.</b> {body}", style))
        return flow
    flow.append(Paragraph(inline(content), styles["para"]))
    return flow


def compile_public():
    src = (DOCS / "centinel-engine-whitepaper-v1.tex").read_text(encoding="utf-8")
    styles = build_styles()
    out = DOCS / "centinel-engine-whitepaper-v1.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, topMargin=22 * mm,
                            bottomMargin=20 * mm, leftMargin=22 * mm,
                            rightMargin=22 * mm, title="Centinela Whitepaper v1.0")
    story = []
    title_done = False
    for kind, payload in parse_latex(src):
        if kind == "title" and not title_done:
            lines = re.split(r"\\\\(?:\[[^\]]*\])?", payload)
            story.append(Paragraph(inline(lines[0]), styles["title"]))
            for ln in lines[1:]:
                t = inline(ln)
                if t:
                    story.append(Paragraph(t, styles["subtitle"]))
            title_done = True
        elif kind == "author":
            story.append(Paragraph(inline(payload), styles["author"]))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                     color=colors.HexColor("#999999")))
            story.append(Spacer(1, 8))
        elif kind == "h1":
            story.append(Paragraph(payload, styles["h1"]))
        elif kind == "h2":
            story.append(Paragraph(payload, styles["h2"]))
        elif kind == "run":
            story.append(Paragraph("<b>" + payload + "</b>", styles["runt"]))
        elif kind == "para":
            story.append(Paragraph(payload, styles["para"]))
        elif kind == "env":
            story.extend(env_to_flow(payload[0], payload[1], styles))
    doc.build(story)
    print(f"OK public  -> {out} ({out.stat().st_size // 1024} KB)")


def compile_internal():
    md = (DOCS / "INTERNAL-whitepaper-es.md").read_text(encoding="utf-8")
    styles = build_styles()
    out = DOCS / "INTERNAL-whitepaper-es.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, topMargin=22 * mm,
                            bottomMargin=20 * mm, leftMargin=22 * mm,
                            rightMargin=22 * mm, title="Centinela Whitepaper Interno")
    story = []

    def md_inline(s):
        s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`([^`]+)`", r'<font face="Mono">\1</font>', s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
        return s.replace("&", "&amp;").replace("&amp;lt;", "&lt;")

    in_table = []
    for raw in md.split("\n"):
        line = raw.rstrip()
        if line.startswith("|") and "---" not in line:
            in_table.append([c.strip() for c in line.strip("|").split("|")])
            continue
        elif in_table:
            rows = [[Paragraph(md_inline(c), styles["para"]) for c in r] for r in in_table]
            ncol = max(len(r) for r in rows)
            rows = [r + [Paragraph("", styles["para"])] * (ncol - len(r)) for r in rows]
            t = Table(rows, hAlign="LEFT")
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))
            in_table = []
        if "---" in line and set(line.strip()) <= {"-"}:
            story.append(HRFlowable(width="100%", thickness=0.5,
                                     color=colors.HexColor("#cccccc")))
        elif line.startswith("# "):
            story.append(Paragraph(md_inline(line[2:]), styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(md_inline(line[3:]), styles["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(md_inline(line[4:]), styles["h2"]))
        elif line.startswith("> "):
            story.append(Paragraph(
                '<font color="#a00000"><b>' + md_inline(line[2:]) + "</b></font>",
                styles["para"]))
        elif re.match(r"^\s*[-*]\s+", line):
            story.append(Paragraph("•&nbsp;&nbsp;" +
                                    md_inline(re.sub(r"^\s*[-*]\s+", "", line)),
                                    styles["para"]))
        elif re.match(r"^\s*\d+\.\s+", line):
            story.append(Paragraph(md_inline(line.strip()), styles["para"]))
        elif line.strip():
            story.append(Paragraph(md_inline(line), styles["para"]))
        else:
            story.append(Spacer(1, 4))
    doc.build(story)
    print(f"OK internal-> {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    compile_public()
    compile_internal()
