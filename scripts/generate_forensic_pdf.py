#!/usr/bin/env python3
"""Generate a PDF executive report using REAL forensic data from Honduras 2025.

Genera un informe ejecutivo PDF usando datos forenses REALES de Honduras 2025.

Unlike generate_report.py (which uses mock data), this script loads all 64
real snapshots from tests/fixtures/hnd_2025/, runs the InconsistentActsTracker
forensic engine, and renders the findings into a multi-page landscape PDF.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — ensure src/ and project root are importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_PROJECT_ROOT))

from auditor.inconsistent_acts import InconsistentActsTracker

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as reportlab_canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Reuse font registration and numbered canvas from generate_report
from scripts.generate_report import NumberedCanvas, _register_pdf_fonts

# ---------------------------------------------------------------------------
# Severity colour maps (same as generate_report.py)
# ---------------------------------------------------------------------------
_SEVERITY_BG = {
    "CRITICAL": "#fdecea",
    "HIGH": "#fff3e0",
    "WARNING": "#fff8e1",
    "MEDIUM": "#e8f0fe",
    "INFO": "#e8f5e9",
}
_SEVERITY_FG = {
    "CRITICAL": "#c62828",
    "HIGH": "#e65100",
    "WARNING": "#f57f17",
    "MEDIUM": "#1a73e8",
    "INFO": "#2e7d32",
}


# ---------------------------------------------------------------------------
# Timestamp parsing (same regex as forensic_hnd_2025.py)
# ---------------------------------------------------------------------------
def parse_timestamp_from_filename(filename: str) -> datetime:
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+(\d{2})_(\d{2})_(\d{2})", filename)
    if not m:
        raise ValueError(f"Cannot parse timestamp from {filename}")
    date_str = m.group(1)
    h, mi, s = m.group(2), m.group(3), m.group(4)
    return datetime.fromisoformat(f"{date_str}T{h}:{mi}:{s}+00:00")


# ---------------------------------------------------------------------------
# Load snapshots and run forensic engine
# ---------------------------------------------------------------------------
def run_forensic_engine(data_dir: Path) -> InconsistentActsTracker:
    """Load all snapshots and return a fully populated tracker."""
    files = sorted(data_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")

    tracker = InconsistentActsTracker(
        config_path=Path("/tmp/forensic_pdf_key.json"),
        runtime_config_path=Path("/tmp/forensic_pdf_config.json"),
        blackout_gap_minutes=30,
        max_resolution_rate=10.0,
        bulk_resolution_threshold=200,
        stagnation_cycles_threshold=4,
        prolonged_stagnation_cycles=8,
    )

    for f in files:
        raw = json.loads(f.read_text(encoding="utf-8"))
        ts = parse_timestamp_from_filename(f.name)
        tracker.load_snapshot(raw, ts)

    return tracker


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------
def build_forensic_pdf(tracker: InconsistentActsTracker, output_path: str) -> None:
    """Build the multi-page forensic PDF report."""
    regular_font, bold_font = _register_pdf_fonts()
    page_size = landscape(A4)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1 * cm,
    )

    # ── Styles ──
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="HeadingPrimary", fontName=bold_font, fontSize=14,
        leading=18, textColor=colors.HexColor("#1F77B4"), spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="HeadingSecondary", fontName=bold_font, fontSize=12,
        leading=15, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Body", fontName=regular_font, fontSize=10, leading=13,
    ))
    styles.add(ParagraphStyle(
        name="BodySmall", fontName=regular_font, fontSize=8, leading=10,
    ))
    styles.add(ParagraphStyle(
        name="TableCell", fontName=regular_font, fontSize=8,
        leading=10, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="TableHeader", fontName=bold_font, fontSize=8,
        leading=10, alignment=TA_CENTER, textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="Disclaimer", fontName=bold_font, fontSize=9,
        leading=12, textColor=colors.HexColor("#856404"),
    ))

    def p(text: str, style_name: str = "Body") -> Paragraph:
        return Paragraph(str(text), styles[style_name])

    def build_table(rows: list, col_widths: list) -> Table:
        header = [p(c, "TableHeader") for c in rows[0]]
        body = [[p(c, "TableCell") for c in row] for row in rows[1:]]
        tbl = Table([header] + body, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F77B4")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d4db")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.whitesmoke, colors.HexColor("#f8fafc")]),
        ]))
        return tbl

    # ── Extract data from tracker ──
    anomalies = tracker.detect_anomalies()
    blackouts = tracker.detect_blackout_windows()
    velocity = tracker.detect_resolution_velocity_anomalies()
    progressive = tracker.detect_progressive_injection()
    asymmetry = tracker.detect_asymmetric_benefit()
    cumulative = tracker.get_special_scrutiny_cumulative()
    snapshots = tracker.snapshots

    elements: list = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1: Executive Summary (Bilingual ES/EN)
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(p("C.E.N.T.I.N.E.L. — Informe Forense: Honduras 2025", "HeadingPrimary"))
    elements.append(Spacer(1, 8))

    elements.append(p("Que es Centinel / What is Centinel", "HeadingSecondary"))
    elements.append(p(
        "Centinel es un motor de auditoria electoral de codigo abierto que monitorea transmisiones "
        "de resultados en tiempo real, detectando anomalias estadisticas mediante analisis forense automatizado. "
        "Centinel is an open-source electoral audit engine that monitors real-time result transmissions, "
        "detecting statistical anomalies through automated forensic analysis."
    ))
    elements.append(Spacer(1, 8))

    elements.append(p("Hallazgos Clave / Key Findings", "HeadingSecondary"))

    first_ts = snapshots[0].timestamp.strftime("%Y-%m-%d %H:%M")
    last_ts = snapshots[-1].timestamp.strftime("%Y-%m-%d %H:%M")
    n_anomalies = len(anomalies)
    n_blackouts = len(blackouts)
    n_velocity = len(velocity)
    total_special = cumulative["total_special_scrutiny_votes"]

    bullet_lines = [
        f"&bull; Periodo analizado: {first_ts} a {last_ts} ({len(snapshots)} snapshots)",
        f"&bull; Anomalias estadisticas detectadas: {n_anomalies}",
        f"&bull; Ventanas de apagon comunicacional: {n_blackouts}",
        f"&bull; Anomalias de velocidad de resolucion: {n_velocity}",
        f"&bull; Votos via escrutinio especial: {total_special:,}",
    ]

    if asymmetry:
        bullet_lines.append(
            f"&bull; Beneficio asimetrico detectado: {asymmetry['beneficiary']} "
            f"(+{asymmetry['swing_pp']} pp, z={asymmetry['z_score']:+.3f})"
        )

    if progressive:
        bullet_lines.append(
            f"&bull; Inyeccion progresiva: {progressive['cycles_count']} ciclos, "
            f"z={progressive['z_score_acumulado']:+.3f}"
        )

    for line in bullet_lines:
        elements.append(p(line))

    elements.append(Spacer(1, 12))

    # Disclaimer box
    disclaimer_table = Table(
        [["AVISO / DISCLAIMER: Este sistema no afirma fraude. Detecta anomalias estadisticas "
          "que requieren investigacion independiente. / This system does not assert fraud. "
          "It detects statistical anomalies that require independent investigation."]],
        colWidths=[doc.width],
    )
    disclaimer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3CD")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#856404")),
        ("FONTNAME", (0, 0), (-1, -1), bold_font),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(disclaimer_table)
    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2: Timeline of Events
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(p("Linea de Tiempo / Timeline of Events", "HeadingPrimary"))
    elements.append(Spacer(1, 4))

    # Build a set of anomaly timestamps for highlighting
    anomaly_ts_set = {a.timestamp for a in anomalies}

    timeline_rows = [["#", "Timestamp", "Actas Inconsistentes", "Votos Totales", "Delta Actas", "Anomalia"]]
    prev_count = None
    for idx, snap in enumerate(snapshots):
        ts_str = snap.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        total_votes = sum(snap.candidate_votes.values())
        delta = snap.inconsistent_count - prev_count if prev_count is not None else 0
        is_anomaly = snap.timestamp in anomaly_ts_set
        timeline_rows.append([
            str(idx + 1),
            ts_str,
            f"{snap.inconsistent_count:,}",
            f"{total_votes:,}",
            f"{delta:+,}" if prev_count is not None else "—",
            "SI" if is_anomaly else "",
        ])
        prev_count = snap.inconsistent_count

    col_w = [doc.width * f for f in [0.04, 0.18, 0.16, 0.16, 0.12, 0.10]]
    timeline_tbl = build_table(timeline_rows, col_w)

    # Highlight anomaly rows with red background
    extra_style = []
    for row_idx in range(1, len(timeline_rows)):
        if timeline_rows[row_idx][5] == "SI":
            extra_style.append(
                ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#fdecea"))
            )
    if extra_style:
        timeline_tbl.setStyle(TableStyle(extra_style))

    elements.append(timeline_tbl)
    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3: Critical Anomalies
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(p("Anomalias Criticas / Critical Anomalies", "HeadingPrimary"))
    elements.append(Spacer(1, 4))

    if anomalies:
        anom_rows = [["Timestamp", "Tipo / Kind", "Severidad", "Descripcion"]]
        for a in anomalies:
            desc = a.message
            if len(desc) > 100:
                desc = desc[:97] + "..."
            anom_rows.append([
                a.timestamp.strftime("%Y-%m-%d %H:%M"),
                a.kind,
                a.severity,
                desc,
            ])
        anom_widths = [doc.width * f for f in [0.15, 0.18, 0.10, 0.57]]
        anom_tbl = build_table(anom_rows, anom_widths)

        # Color-code by severity
        sev_styles = []
        for row_idx, row in enumerate(anom_rows[1:], start=1):
            sev = row[2].upper()
            if sev in _SEVERITY_BG:
                sev_styles.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor(_SEVERITY_BG[sev]))
                )
                sev_styles.append(
                    ("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.HexColor(_SEVERITY_FG[sev]))
                )
        if sev_styles:
            anom_tbl.setStyle(TableStyle(sev_styles))

        elements.append(anom_tbl)
    else:
        elements.append(p("No se detectaron anomalias. / No anomalies detected."))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4: Blackout Analysis
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(p("Analisis de Apagones / Blackout Analysis", "HeadingPrimary"))
    elements.append(Spacer(1, 4))
    elements.append(p(
        "Ventanas donde la transmision de resultados se detuvo por mas de 30 minutos. "
        "/ Windows where result transmission stopped for more than 30 minutes."
    ))
    elements.append(Spacer(1, 6))

    if blackouts:
        # Filter for significant blackouts (>= 120 min)
        significant = [b for b in blackouts if b["gap_minutes"] >= 120]
        if not significant:
            significant = blackouts  # show all if none > 2h

        bo_rows = [["Inicio / Start", "Fin / End", "Duracion (min)", "Cambios de Tendencia / Trend Shifts"]]
        for b in significant:
            shifts = ""
            if b.get("trend_shifts_pp"):
                parts = [f"{c}: {s:+.3f} pp" for c, s in sorted(b["trend_shifts_pp"].items())]
                shifts = "; ".join(parts)
            bo_rows.append([
                str(b["gap_start"]),
                str(b["gap_end"]),
                str(b["gap_minutes"]),
                shifts or "—",
            ])
        bo_widths = [doc.width * f for f in [0.22, 0.22, 0.12, 0.44]]
        bo_tbl = build_table(bo_rows, bo_widths)

        # Highlight overnight gaps (> 6 hours)
        overnight_styles = []
        for row_idx, b in enumerate(significant, start=1):
            if b["gap_minutes"] >= 360:
                overnight_styles.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#fff3e0"))
                )
        if overnight_styles:
            bo_tbl.setStyle(TableStyle(overnight_styles))

        elements.append(bo_tbl)
    else:
        elements.append(p("No se detectaron ventanas de apagon. / No blackout windows detected."))

    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5: Statistical Summary
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(p("Resumen Estadistico / Statistical Summary", "HeadingPrimary"))
    elements.append(Spacer(1, 6))

    # Velocity anomalies
    elements.append(p("Anomalias de Velocidad / Velocity Anomalies", "HeadingSecondary"))
    if velocity:
        vel_rows = [["Timestamp", "Actas Resueltas", "Minutos", "Tasa (actas/min)"]]
        for v in velocity:
            vel_rows.append([
                str(v["timestamp"]),
                str(v["delta_actas"]),
                f"{v['elapsed_minutes']:.1f}",
                f"{v['rate_per_minute']:.1f}",
            ])
        vel_widths = [doc.width * f for f in [0.25, 0.20, 0.20, 0.20]]
        elements.append(build_table(vel_rows, vel_widths))
    else:
        elements.append(p("No se detectaron anomalias de velocidad. / No velocity anomalies detected."))
    elements.append(Spacer(1, 10))

    # Progressive injection
    elements.append(p("Inyeccion Progresiva / Progressive Injection", "HeadingSecondary"))
    if progressive:
        prog_rows = [["Metrica / Metric", "Valor / Value"]]
        prog_rows.append(["Ciclos detectados / Cycles", str(progressive["cycles_count"])])
        prog_rows.append(["Promedio delta/ciclo / Avg delta/cycle", f"{progressive['avg_delta_per_cycle']:.2f}"])
        prog_rows.append(["Z-score acumulado", f"{progressive['z_score_acumulado']:+.3f}"])
        prog_rows.append(["P-value", f"{progressive['z_score_pvalue']:.5f}"])
        prog_widths = [doc.width * 0.4, doc.width * 0.4]
        elements.append(build_table(prog_rows, prog_widths))
    else:
        elements.append(p("No se detecto inyeccion progresiva. / No progressive injection detected."))
    elements.append(Spacer(1, 10))

    # Candidate vote progression
    elements.append(p("Progresion de Votos por Candidato / Candidate Vote Progression", "HeadingSecondary"))
    first_snap = snapshots[0]
    last_snap = snapshots[-1]
    cand_rows = [["Candidato", "Primer Snapshot", "Ultimo Snapshot", "Delta", "Escrutinio Especial"]]
    all_candidates = sorted(set(list(first_snap.candidate_votes.keys()) + list(last_snap.candidate_votes.keys())))
    for cand in all_candidates:
        v_first = first_snap.candidate_votes.get(cand, 0)
        v_last = last_snap.candidate_votes.get(cand, 0)
        special = cumulative["votes_by_candidate"].get(cand, 0)
        cand_rows.append([
            cand,
            f"{v_first:,}",
            f"{v_last:,}",
            f"{v_last - v_first:+,}",
            f"{special:+,}",
        ])
    cand_widths = [doc.width * f for f in [0.28, 0.15, 0.15, 0.15, 0.17]]
    elements.append(build_table(cand_rows, cand_widths))
    elements.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 6: Cryptographic Verification
    # ══════════════════════════════════════════════════════════════════════════
    elements.append(p("Verificacion Criptografica / Cryptographic Verification", "HeadingPrimary"))
    elements.append(Spacer(1, 6))

    gen_ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    elements.append(p(f"Reporte generado: {gen_ts}"))
    elements.append(p(
        "Metodologia: Motor forense InconsistentActsTracker v1.0 — analisis de 64 snapshots reales "
        "del sitio resultadosgenerales2025.cne.hn capturados entre el 3 y 8 de diciembre de 2025."
    ))
    elements.append(Spacer(1, 8))

    elements.append(p("SHA-256 de Snapshots Fuente / Source Snapshot Hashes", "HeadingSecondary"))

    hash_rows = [["#", "Timestamp", "SHA-256"]]
    for idx, snap in enumerate(snapshots):
        hash_rows.append([
            str(idx + 1),
            snap.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            snap.source_hash[:32] + "...",
        ])
    hash_widths = [doc.width * 0.05, doc.width * 0.20, doc.width * 0.55]
    hash_tbl = build_table(hash_rows, hash_widths)
    elements.append(hash_tbl)
    elements.append(Spacer(1, 10))

    # Compute composite hash of all snapshot hashes
    composite_input = "|".join(s.source_hash for s in snapshots)
    composite_hash = hashlib.sha256(composite_input.encode("utf-8")).hexdigest()
    elements.append(p(f"Hash compuesto del dataset: {composite_hash}", "BodySmall"))
    elements.append(p(
        "Para verificar, ejecute: make reproduce-2025-audit", "BodySmall"
    ))

    # ── Footer callback ──
    def draw_footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(1.5 * cm, 0.75 * cm, "C.E.N.T.I.N.E.L. — Informe Forense Honduras 2025")
        canvas.drawRightString(
            page_size[0] - 1.5 * cm, 0.75 * cm,
            f"Generado: {gen_ts}",
        )
        canvas.setFont(regular_font, 7)
        canvas.drawString(
            1.5 * cm, 0.45 * cm,
            "Este sistema no afirma fraude. Detecta anomalias estadisticas.",
        )
        # Watermark
        canvas.setFont(bold_font, 32)
        canvas.setFillColor(colors.Color(0.12, 0.4, 0.6, alpha=0.08))
        canvas.drawCentredString(page_size[0] / 2, page_size[1] / 2, "VERIFICABLE")
        canvas.restoreState()

    doc.build(
        elements,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
        canvasmaker=NumberedCanvas,
    )

    pdf_bytes = buffer.getvalue()
    Path(output_path).write_bytes(pdf_bytes)
    return len(pdf_bytes)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate forensic PDF report from real HND-2025 data"
    )
    parser.add_argument(
        "--output", default="centinel_hnd_2025_forensic.pdf",
        help="Output PDF path (default: centinel_hnd_2025_forensic.pdf)",
    )
    args = parser.parse_args()

    data_dir = _PROJECT_ROOT / "tests" / "fixtures" / "hnd_2025"
    print(f"Loading snapshots from {data_dir} ...")
    tracker = run_forensic_engine(data_dir)
    print(f"  Loaded {len(tracker.snapshots)} snapshots")
    print(f"  Detected key: {tracker.detected_inconsistent_key}")
    print(f"  Events: {len(tracker.events)}")

    anomalies = tracker.detect_anomalies()
    blackouts = tracker.detect_blackout_windows()
    velocity = tracker.detect_resolution_velocity_anomalies()
    cumulative = tracker.get_special_scrutiny_cumulative()

    print(f"\n  Anomalies: {len(anomalies)}")
    print(f"  Blackout windows: {len(blackouts)}")
    print(f"  Velocity anomalies: {len(velocity)}")
    print(f"  Special scrutiny votes: {cumulative['total_special_scrutiny_votes']:,}")

    print(f"\nGenerating PDF -> {args.output} ...")
    size = build_forensic_pdf(tracker, args.output)
    print(f"  PDF written: {args.output} ({size:,} bytes)")


if __name__ == "__main__":
    main()
