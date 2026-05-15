#!/usr/bin/env python
"""
Generate PDF versions of Centinel whitepapers from source files.

This script converts:
1. centinel-engine-whitepaper-v1.tex (LaTeX) → centinel-engine-whitepaper-v1.pdf
2. INTERNAL-whitepaper-es.md (Markdown) → INTERNAL-whitepaper-es.pdf

Usage:
    python scripts/generate_whitepapers_pdf.py
"""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs" / "whitepaper"


def read_latex_content() -> str:
    """Read and extract text content from LaTeX source."""
    tex_file = DOCS_DIR / "centinel-engine-whitepaper-v1.tex"
    if not tex_file.exists():
        print(f"Error: {tex_file} not found")
        return ""

    with open(tex_file) as f:
        content = f.read()

    # Simple extraction: remove LaTeX commands but preserve structure
    lines = []
    skip_mode = False
    for line in content.split('\n'):
        # Skip preamble and special sections
        if '\\documentclass' in line or '\\usepackage' in line:
            skip_mode = True
        elif '\\begin{document}' in line:
            skip_mode = False
            continue
        elif '\\end{document}' in line:
            break
        elif skip_mode:
            continue

        # Remove common LaTeX commands
        line = line.replace('\\\\', ' ')
        line = line.replace('\\textbf{', '').replace('}', '')
        line = line.replace('\\emph{', '').replace('}', '')
        line = line.replace('\\cite{', '[')
        line = line.replace('\\ref{', '[Ref: ')
        line = line.replace('\\section{', '## ').replace('}', '')
        line = line.replace('\\subsection{', '### ').replace('}', '')
        line = line.replace('\\subsubsection{', '#### ').replace('}', '')

        if line.strip():
            lines.append(line.strip())

    return '\n'.join(lines)


def read_markdown_content() -> str:
    """Read Markdown content."""
    md_file = DOCS_DIR / "INTERNAL-whitepaper-es.md"
    if not md_file.exists():
        print(f"Error: {md_file} not found")
        return ""

    with open(md_file) as f:
        return f.read()


def markdown_to_paragraphs(text: str, styles: object) -> list:
    """Convert Markdown text to ReportLab Paragraph objects."""
    paragraphs = []
    heading_style = styles['Heading1']
    body_style = styles['BodyText']

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            paragraphs.append(Spacer(1, 0.1 * inch))
            continue

        # Check for Markdown headings
        if line.startswith('# '):
            title = line[2:].strip()
            para = Paragraph(f"<b>{title}</b>", heading_style)
            paragraphs.append(para)
            paragraphs.append(Spacer(1, 0.1 * inch))
        elif line.startswith('## '):
            subtitle = line[3:].strip()
            para = Paragraph(f"<i>{subtitle}</i>", heading_style)
            paragraphs.append(para)
            paragraphs.append(Spacer(1, 0.05 * inch))
        elif line.startswith('> '):
            quote = line[2:].strip()
            para = Paragraph(f'<font color="darkblue"><i>"{quote}"</i></font>', body_style)
            paragraphs.append(para)
        else:
            para = Paragraph(line, body_style)
            paragraphs.append(para)

    return paragraphs


def generate_public_whitepaper_pdf():
    """Generate PDF for public whitepaper."""
    output_file = DOCS_DIR / "centinel-engine-whitepaper-v1.pdf"

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomBody', parent=styles['Normal'], fontSize=10, leading=14))

    story = []

    # Title
    title = Paragraph("<b>Centinel Engine: Certificate Transparency for Electoral Custody</b>", styles['Heading1'])
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))

    # Subtitle
    subtitle = Paragraph("System Design, Threat Model, and Validation", styles['Heading3'])
    story.append(subtitle)
    story.append(Spacer(1, 0.15 * inch))

    # Abstract
    abstract_heading = Paragraph("<b>Abstract</b>", styles['Heading2'])
    story.append(abstract_heading)
    abstract_text = Paragraph(
        "Centinel applies the Certificate Transparency model (RFC 6962) to electoral data custody under a "
        "reversed threat model where the electoral authority itself is the adversary. We formalize three theorems: "
        "(T1) tamper-evidence via hash-chain collision resistance, (T2) authenticity via Ed25519 signatures, and "
        "(T3) rewrite detection via Merkle root anchoring to external append-only ledgers (Bitcoin via OpenTimestamps). "
        "The system is zero-cost, country-agnostic, and reproducible by third-party observers without trusting any "
        "single entity. We discuss deployment in Honduras 2028 and lessons for electoral integrity globally.",
        styles['CustomBody']
    )
    story.append(abstract_text)
    story.append(Spacer(1, 0.2 * inch))

    # Extract content
    latex_content = read_latex_content()
    if latex_content:
        paragraphs = markdown_to_paragraphs(latex_content, styles)
        story.extend(paragraphs)

    # Build PDF
    try:
        doc.build(story)
        print(f"✓ Generated: {output_file}")
        return True
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        return False


def generate_internal_whitepaper_pdf():
    """Generate PDF for internal Spanish whitepaper."""
    output_file = DOCS_DIR / "INTERNAL-whitepaper-es.pdf"

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomBody', parent=styles['Normal'], fontSize=10, leading=14))

    story = []

    # Title
    title = Paragraph("<b>Centinela — Whitepaper INTERNO (ES)</b>", styles['Heading1'])
    story.append(title)
    story.append(Spacer(1, 0.1 * inch))

    # Warning
    warning = Paragraph(
        '<font color="red"><b>⚠ NO DISTRIBUIR. CONSUMO PROPIO.</b></font><br/>'
        'Este documento es la versión cruda y estratégica para decisiones internas.',
        styles['CustomBody']
    )
    story.append(warning)
    story.append(Spacer(1, 0.15 * inch))

    # Content
    md_content = read_markdown_content()
    if md_content:
        paragraphs = markdown_to_paragraphs(md_content, styles)
        story.extend(paragraphs)

    # Build PDF
    try:
        doc.build(story)
        print(f"✓ Generated: {output_file}")
        return True
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        return False


def main():
    """Generate both whitepapers."""
    print("Generating Centinel whitepapers as PDFs...\n")

    public_ok = generate_public_whitepaper_pdf()
    internal_ok = generate_internal_whitepaper_pdf()

    print()
    if public_ok and internal_ok:
        print("✓ All whitepapers generated successfully.")
        print(f"\nOutput files:")
        print(f"  - {DOCS_DIR / 'centinel-engine-whitepaper-v1.pdf'}")
        print(f"  - {DOCS_DIR / 'INTERNAL-whitepaper-es.pdf'}")
        return 0
    else:
        print("✗ Some whitepapers failed to generate.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
