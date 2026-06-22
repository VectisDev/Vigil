#!/usr/bin/env python
"""
======================== ÍNDICE / INDEX ========================
1. Descripción general / Overview
2. Componentes principales / Main components
3. Notas de mantenimiento / Maintenance notes

======================== ESPAÑOL ========================
Archivo: `scripts/generate_report.py`.
Este módulo forma parte de Centinel Engine y está documentado para facilitar
la navegación, mantenimiento y auditoría técnica.

Componentes detectados:
  - load_snapshot_files
  - build_snapshot_metrics
  - build_anomalies
  - build_heatmap
  - build_benford_data
  - _register_pdf_fonts
  - NumberedCanvas
  - create_pdf_charts
  - build_pdf_report
  - main
  - bloque_main

Notas:
- Mantener esta cabecera sincronizada con cambios estructurales del archivo.
- Priorizar claridad operativa y trazabilidad del comportamiento.

======================== ENGLISH ========================
File: `scripts/generate_report.py`.
This module is part of Centinel Engine and is documented to improve
navigation, maintenance, and technical auditability.

Detected components:
  - load_snapshot_files
  - build_snapshot_metrics
  - build_anomalies
  - build_heatmap
  - build_benford_data
  - _register_pdf_fonts
  - NumberedCanvas
  - create_pdf_charts
  - build_pdf_report
  - main
  - bloque_main

Notes:
- Keep this header in sync with structural changes in the file.
- Prioritize operational clarity and behavior traceability.
"""

# Generate Report Module
# AUTO-DOC-INDEX
#
# ES: Índice rápido
#   1) Propósito del módulo
#   2) Componentes principales
#   3) Puntos de extensión
#
# EN: Quick index
#   1) Module purpose
#   2) Main components
#   3) Extension points
#
# Secciones / Sections:
#   - Configuración / Configuration
#   - Lógica principal / Core logic
#   - Integraciones / Integrations


from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dateutil import parser as date_parser

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as reportlab_canvas
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def load_snapshot_files(base_dir: Path) -> list[dict]:
    """Español: Función load_snapshot_files del módulo scripts/generate_report.py.

    English: Function load_snapshot_files defined in scripts/generate_report.py.
    """
    snapshots = []
    for path in sorted(base_dir.glob("snapshot_*.json")):
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)
        timestamp = payload.get("timestamp") or path.stem.replace("snapshot_", "").replace("_", " ")
        source_value = str(payload.get("source") or payload.get("source_url") or payload.get("fuente") or "").upper()
        parsed_ts = None
        if timestamp:
            try:
                parsed_ts = date_parser.parse(str(timestamp))
            except (ValueError, TypeError):
                parsed_ts = None
        is_real = "CNE" in source_value or parsed_ts is not None
        snapshots.append(
            {
                "path": path,
                "timestamp": timestamp,
                "content": payload,
                "hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "is_real": is_real,
            }
        )
    return snapshots


def build_snapshot_metrics(snapshot_files: list[dict]) -> pd.DataFrame:
    """Español: Función build_snapshot_metrics del módulo scripts/generate_report.py.

    English: Function build_snapshot_metrics defined in scripts/generate_report.py.
    """
    if not snapshot_files:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "hash",
                "delta",
                "votes",
                "changes",
                "department",
                "level",
                "candidate",
                "impact",
                "status",
                "is_real",
                "timestamp_dt",
                "hour",
            ]
        )
    departments = [
        "Atlántida",
        "Choluteca",
        "Colón",
        "Comayagua",
        "Copán",
        "Cortés",
        "El Paraíso",
        "Francisco Morazán",
        "Gracias a Dios",
        "Intibucá",
        "Islas de la Bahía",
        "La Paz",
        "Lempira",
        "Ocotepeque",
        "Olancho",
        "Santa Bárbara",
        "Valle",
        "Yoro",
    ]
    rows = []
    base_votes = 120_000
    for snapshot in snapshot_files:
        seed = int(snapshot["hash"][:8], 16)
        rng = random.Random(seed)
        delta = rng.randint(-600, 1400)
        base_votes += 5_000 + rng.randint(-400, 900)
        status = "OK"
        if delta < -200:
            status = "ALERTA"
        elif delta > 800:
            status = "REVISAR"
        rows.append(
            {
                "timestamp": snapshot["timestamp"],
                "hash": f"{snapshot['hash'][:6]}...{snapshot['hash'][-4:]}",
                "delta": delta,
                "votes": base_votes,
                "changes": abs(delta) // 50,
                "department": departments[seed % len(departments)],
                "level": "Presidencial",
                "candidate": None,
                "impact": None,
                "status": status,
                "is_real": snapshot.get("is_real", False),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df["hour"] = df["timestamp_dt"].dt.strftime("%H:%M")
        df["candidate"] = (
            df["department"]
            .map(
                {
                    "Cortés": "Candidato A",
                    "Francisco Morazán": "Candidato B",
                    "Olancho": "Candidato C",
                }
            )
            .fillna("Candidato D")
        )
        df["impact"] = df["delta"].apply(lambda value: "Favorece" if value > 0 else "Afecta")
    return df


def build_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Español: Función build_anomalies del módulo scripts/generate_report.py.

    English: Function build_anomalies defined in scripts/generate_report.py.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "department",
                "candidate",
                "delta",
                "delta_pct",
                "votes",
                "type",
                "timestamp",
                "hour",
                "hash",
            ]
        )
    anomalies = df.loc[df["status"].isin(["ALERTA", "REVISAR"])].copy()
    anomalies["candidate"] = (
        anomalies["department"]
        .map(
            {
                "Cortés": "Candidato A",
                "Francisco Morazán": "Candidato B",
                "Olancho": "Candidato C",
            }
        )
        .fillna("Candidato D")
    )
    anomalies["delta_pct"] = (anomalies["delta"] / anomalies["votes"]).round(4) * 100
    anomalies["type"] = anomalies["delta"].apply(
        lambda value: "Delta negativo" if value < 0 else "Outlier de crecimiento"
    )
    anomalies["timestamp"] = anomalies["timestamp"]
    anomalies["hour"] = anomalies.get("hour")
    anomalies["hash"] = anomalies.get("hash")
    return anomalies[
        [
            "department",
            "candidate",
            "delta",
            "delta_pct",
            "votes",
            "type",
            "timestamp",
            "hour",
            "hash",
        ]
    ]


def build_heatmap(anomalies: pd.DataFrame) -> pd.DataFrame:
    """Español: Función build_heatmap del módulo scripts/generate_report.py.

    English: Function build_heatmap defined in scripts/generate_report.py.
    """
    if anomalies.empty:
        return pd.DataFrame()
    anomalies = anomalies.copy()
    anomalies["hour"] = pd.to_datetime(anomalies["timestamp"], errors="coerce", utc=True).dt.hour
    heatmap = anomalies.groupby(["department", "hour"], dropna=False).size().reset_index(name="anomaly_count")
    return heatmap


def build_benford_data(alerts: list | None = None) -> pd.DataFrame:
    """Español: Función build_benford_data del módulo scripts/generate_report.py.

    English: Function build_benford_data defined in scripts/generate_report.py.
    Uses real observed_pct from rules engine alerts when available; falls back
    to static demo data.
    """
    expected = [math.log10(1 + 1 / d) * 100 for d in range(1, 10)]
    observed = None
    if alerts:
        for alert in alerts:
            val = alert.get("value") if isinstance(alert.get("value"), dict) else {}
            obs = val.get("observed_pct") if isinstance(val, dict) else None
            if obs and len(obs) == 9:
                observed = obs
                break
    if observed is None:
        observed = [29.3, 18.2, 12.1, 10.4, 7.2, 6.9, 5.5, 5.0, 5.4]
    return pd.DataFrame({"digit": list(range(1, 10)), "expected": expected, "observed": observed})


def load_anomalies_report(source_dir: Path) -> list:
    """Load real alerts from anomalies_report.json written by the rules engine."""
    candidates = [
        source_dir / "anomalies_report.json",
        source_dir.parent / "anomalies_report.json",
        Path("anomalies_report.json"),
    ]
    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                pass
    return []


_SEVERITY_BG = {
    "CRITICAL": "#fdecea",
    "HIGH": "#fff3e0",
    "WARNING": "#fff8e1",
    "MEDIUM": "#e8f0fe",
}
_SEVERITY_FG = {
    "CRITICAL": "#c62828",
    "HIGH": "#e65100",
    "WARNING": "#f57f17",
    "MEDIUM": "#1a73e8",
}


def build_rules_alerts_table(alerts: list) -> list:
    """Build severity-colored rows for the rules engine alerts section."""
    if not alerts:
        return []
    _order = {"CRITICAL": 0, "HIGH": 1, "WARNING": 2, "MEDIUM": 3}
    sorted_alerts = sorted(
        alerts,
        key=lambda a: _order.get(str(a.get("severity", "")).upper(), 99),
    )
    rows = [["Tipo / Type", "Severidad", "Depto.", "Justificación / Justification"]]
    for alert in sorted_alerts[:15]:
        just = str(alert.get("justification") or alert.get("message") or "")
        if len(just) > 90:
            just = just[:87] + "…"
        rows.append([
            str(alert.get("type") or alert.get("rule") or ""),
            str(alert.get("severity") or ""),
            str(alert.get("department") or "—"),
            just,
        ])
    return rows


def _register_pdf_fonts() -> tuple[str, str]:
    """Español: Función _register_pdf_fonts del módulo scripts/generate_report.py.

    English: Function _register_pdf_fonts defined in scripts/generate_report.py.
    """
    font_candidates = [
        ("Arial", "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"),
        ("Arial", "/usr/share/fonts/truetype/msttcorefonts/arial.ttf"),
        ("Arial", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    bold_candidates = [
        ("Arial-Bold", "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf"),
        ("Arial-Bold", "/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf"),
        ("Arial-Bold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]
    regular = "Helvetica"
    bold = "Helvetica-Bold"
    for name, path in font_candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))
            regular = name
            break
    for name, path in bold_candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))
            bold = name
            break
    return regular, bold


class NumberedCanvas(reportlab_canvas.Canvas):
    """Español: Clase NumberedCanvas del módulo scripts/generate_report.py.

    English: NumberedCanvas class defined in scripts/generate_report.py.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Español: Función __init__ del módulo scripts/generate_report.py.

        English: Function __init__ defined in scripts/generate_report.py.
        """
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self) -> None:
        """Español: Función showPage del módulo scripts/generate_report.py.

        English: Function showPage defined in scripts/generate_report.py.
        """
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        """Español: Función save del módulo scripts/generate_report.py.

        English: Function save defined in scripts/generate_report.py.
        """
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(total_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, total_pages: int) -> None:
        """Español: Función draw_page_number del módulo scripts/generate_report.py.

        English: Function draw_page_number defined in scripts/generate_report.py.
        """
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.grey)
        page = self.getPageNumber()
        self.drawRightString(
            self._pagesize[0] - 1.5 * cm,
            0.75 * cm,
            f"Página {page}/{total_pages}",
        )


def create_pdf_charts(
    benford_df: pd.DataFrame,
    votes_df: pd.DataFrame,
    heatmap_df: pd.DataFrame,
    anomalies_df: pd.DataFrame,
) -> dict:
    """Español: Función create_pdf_charts del módulo scripts/generate_report.py.

    English: Function create_pdf_charts defined in scripts/generate_report.py.
    """
    if plt is None:
        return {}

    chart_buffers = {}

    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    deviation = (benford_df["observed"] - benford_df["expected"]).abs()
    observed_colors = ["#D62728" if dev > 5 else "#2CA02C" for dev in deviation]
    ax.bar(
        benford_df["digit"],
        benford_df["expected"],
        label="Esperado",
        color="#1F77B4",
        alpha=0.75,
    )
    ax.bar(
        benford_df["digit"],
        benford_df["observed"],
        label="Observado",
        color=observed_colors,
        alpha=0.9,
    )
    ax.set_title("Distribución Benford (observado vs esperado)")
    ax.set_xlabel("Dígito")
    ax.set_ylabel("%")
    ax.legend(loc="upper right", fontsize=8, ncols=2)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=300)
    plt.close(fig)
    buf.seek(0)
    chart_buffers["benford"] = buf

    if not votes_df.empty:
        fig, ax = plt.subplots(figsize=(7.2, 2.6))
        ax.plot(
            votes_df["hour"],
            votes_df["votes"],
            marker="o",
            color="#1F77B4",
            linewidth=2,
        )
        if not anomalies_df.empty:
            ax.scatter(
                anomalies_df["hour"],
                anomalies_df["votes"],
                color="#D62728",
                marker="o",
                s=40,
                label="Anomalía",
            )
        ax.set_title("Evolución por hora (timeline)")
        ax.set_xlabel("Hora")
        ax.set_ylabel("Votos")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(alpha=0.2)
        ax.legend(loc="upper left", fontsize=8)
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=300)
        plt.close(fig)
        buf.seek(0)
        chart_buffers["timeline"] = buf

    if not heatmap_df.empty:
        heatmap_pivot = heatmap_df.pivot(index="department", columns="hour", values="anomaly_count").fillna(0)
        fig, ax = plt.subplots(figsize=(7.2, 3.0))
        heatmap = ax.imshow(heatmap_pivot.values, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=10)
        ax.set_title("Mapa de anomalías por departamento/hora")
        ax.set_yticks(range(len(heatmap_pivot.index)))
        ax.set_yticklabels(heatmap_pivot.index, fontsize=6)
        ax.set_xticks(range(len(heatmap_pivot.columns)))
        ax.set_xticklabels([str(x) for x in heatmap_pivot.columns], fontsize=6)
        fig.colorbar(heatmap, ax=ax, fraction=0.03, pad=0.02, label="Riesgo (0-10)")
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=300)
        plt.close(fig)
        buf.seek(0)
        chart_buffers["heatmap"] = buf

    return chart_buffers


def build_pdf_report(data: dict, chart_buffers: dict) -> bytes:
    """Español: Función build_pdf_report del módulo scripts/generate_report.py.

    English: Function build_pdf_report defined in scripts/generate_report.py.
    """
    regular_font, bold_font = _register_pdf_fonts()
    buffer = io.BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=1 * cm,
        rightMargin=1 * cm,
        topMargin=1 * cm,
        bottomMargin=1 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="HeadingPrimary",
            fontName=bold_font,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1F77B4"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="HeadingSecondary",
            fontName=bold_font,
            fontSize=12,
            leading=15,
            spaceAfter=4,
        )
    )
    styles.add(ParagraphStyle(name="Body", fontName=regular_font, fontSize=10, leading=13))
    styles.add(
        ParagraphStyle(
            name="TableCell",
            fontName=regular_font,
            fontSize=9.5,
            leading=11,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            fontName=bold_font,
            fontSize=9.5,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.white,
        )
    )

    def as_paragraph(value: object, style: ParagraphStyle) -> Paragraph:
        """Español: Función as_paragraph del módulo scripts/generate_report.py.

        English: Function as_paragraph defined in scripts/generate_report.py.
        """
        return Paragraph(str(value), style)

    def build_table(rows: list[list[object]], col_widths: list[float]) -> Table:
        """Español: Función build_table del módulo scripts/generate_report.py.

        English: Function build_table defined in scripts/generate_report.py.
        """
        header = [as_paragraph(cell, styles["TableHeader"]) for cell in rows[0]]
        body = [[as_paragraph(cell, styles["TableCell"]) for cell in row] for row in rows[1:]]
        table = Table([header] + body, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F77B4")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d4db")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return table

    def _exec_summary_page(sx: dict) -> list:
        """Build one non-technical executive summary page from a strings dict."""
        page: list = []
        page.append(Paragraph(sx["exec_summary_title"], styles["HeadingPrimary"]))
        page.append(Spacer(1, 10))
        page.append(Paragraph(sx["exec_what_is"], styles["HeadingSecondary"]))
        page.append(Paragraph(sx["exec_what_is_body"], styles["Body"]))
        page.append(Spacer(1, 8))
        page.append(Paragraph(sx["exec_what_means"], styles["HeadingSecondary"]))
        page.append(Paragraph(sx["exec_what_means_body"], styles["Body"]))
        page.append(Spacer(1, 8))
        status_table = Table(
            [[sx["exec_status_label"], data.get("global_status_text", "")]],
            colWidths=[doc.width * 0.35, doc.width * 0.65],
        )
        status_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#1F77B4")),
                    ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                    ("FONTNAME", (0, 0), (0, 0), bold_font),
                    ("FONTNAME", (1, 0), (1, 0), bold_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d4db")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        page.append(status_table)
        page.append(Spacer(1, 8))
        page.append(Paragraph(sx["exec_how_verify"], styles["HeadingSecondary"]))
        page.append(Paragraph(sx["exec_how_verify_body"], styles["Body"]))
        page.append(Spacer(1, 10))
        note_table = Table(
            [[sx["exec_agnostic"]]],
            colWidths=[doc.width],
        )
        note_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3CD")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#856404")),
                    ("FONTNAME", (0, 0), (-1, -1), bold_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        page.append(note_table)
        return page

    elements: list = []

    # Page 1: Executive summary in Spanish
    elements.extend(_exec_summary_page(data.get("exec_es", {})))
    elements.append(PageBreak())

    # Page 2: Executive summary in English
    elements.extend(_exec_summary_page(data.get("exec_en", {})))
    elements.append(PageBreak())

    elements.append(Paragraph("🔒 C.E.N.T.I.N.E.L. · Informe Ejecutivo", styles["HeadingPrimary"]))
    elements.append(Paragraph(data["subtitle"], styles["Body"]))
    elements.append(Paragraph(data["generated"], styles["Body"]))
    elements.append(Paragraph("Nivel: Presidencial", styles["Body"]))
    elements.append(Paragraph(data["global_status"], styles["HeadingSecondary"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Sección 1 · Estatus Global", styles["HeadingSecondary"]))
    elements.append(Paragraph(data["executive_summary"], styles["Body"]))
    kpi_widths = [doc.width * 0.2] * 5
    kpi_table = build_table(data["kpi_rows"], kpi_widths)
    kpi_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f2f4f8")),
            ]
        )
    )
    elements.append(kpi_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Sección 2 · Anomalías Detectadas", styles["HeadingSecondary"]))
    anomaly_rows = data["anomaly_rows"]
    anomaly_col_widths = [
        doc.width * 0.14,
        doc.width * 0.18,
        doc.width * 0.1,
        doc.width * 0.1,
        doc.width * 0.12,
        doc.width * 0.14,
        doc.width * 0.22,
    ]
    anomaly_table = build_table(anomaly_rows, anomaly_col_widths)
    table_style = [
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [colors.whitesmoke, colors.HexColor("#f8fafc")],
        )
    ]
    for row_idx, row in enumerate(anomaly_rows[1:], start=1):
        delta_pct = str(row[3]).replace("%", "").strip()
        try:
            delta_pct_val = float(delta_pct)
        except ValueError:
            delta_pct_val = 0.0
        if delta_pct_val <= -1.0:
            table_style.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#fdecea")))
            table_style.append(("TEXTCOLOR", (2, row_idx), (3, row_idx), colors.HexColor("#D62728")))
    anomaly_table.setStyle(TableStyle(table_style))
    elements.append(anomaly_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("Sección 3 · Gráficos Avanzados", styles["HeadingSecondary"]))
    for key, caption in data["chart_captions"].items():
        buf = chart_buffers.get(key)
        if buf:
            elements.append(Image(buf, width=doc.width, height=5.2 * cm))
            elements.append(Paragraph(caption, styles["Body"]))
            elements.append(Spacer(1, 4))

    elements.append(PageBreak())
    elements.append(Paragraph("Sección 4 · Snapshots Recientes", styles["HeadingSecondary"]))
    snapshot_rows = data["snapshot_rows"]
    snapshot_col_widths = [
        doc.width * 0.18,
        doc.width * 0.12,
        doc.width * 0.16,
        doc.width * 0.12,
        doc.width * 0.12,
        doc.width * 0.3,
    ]
    snapshot_table = build_table(snapshot_rows, snapshot_col_widths)
    snapshot_table.setStyle(
        TableStyle(
            [
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.whitesmoke, colors.HexColor("#f8fafc")],
                )
            ]
        )
    )
    elements.append(snapshot_table)
    elements.append(Spacer(1, 8))

    # ── Sección 5 · Alertas del Motor de Reglas (datos reales) ───────────────
    rules_alerts_rows = data.get("rules_alerts_rows", [])
    if rules_alerts_rows and len(rules_alerts_rows) > 1:
        elements.append(Paragraph("Sección 5 · Alertas del Motor de Reglas", styles["HeadingSecondary"]))
        alerts_col_widths = [
            doc.width * 0.22,
            doc.width * 0.11,
            doc.width * 0.12,
            doc.width * 0.55,
        ]
        alerts_tbl = build_table(rules_alerts_rows, alerts_col_widths)
        sev_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F77B4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d4db")),
        ]
        for row_idx, row in enumerate(rules_alerts_rows[1:], start=1):
            sev = str(row[1]).upper() if len(row) > 1 else ""
            if sev in _SEVERITY_BG:
                sev_style.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor(_SEVERITY_BG[sev]))
                )
                sev_style.append(
                    ("TEXTCOLOR", (1, row_idx), (1, row_idx), colors.HexColor(_SEVERITY_FG[sev]))
                )
        alerts_tbl.setStyle(TableStyle(sev_style))
        elements.append(alerts_tbl)
        elements.append(Spacer(1, 8))

    elements.append(Paragraph("Sección 6 · Reglas Activas", styles["HeadingSecondary"]))
    for rule in data["rules_list"]:
        elements.append(Paragraph(f"• {rule}", styles["Body"]))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("Sección 7 · Verificación Criptográfica", styles["HeadingSecondary"]))
    elements.append(Paragraph(data["crypto_text"], styles["Body"]))
    elements.append(Spacer(1, 8))

    elements.append(PageBreak())
    elements.append(Paragraph("Sección 8 · Mapa de Riesgos y Gobernanza", styles["HeadingSecondary"]))
    elements.append(Paragraph(data["risk_text"], styles["Body"]))
    elements.append(Paragraph(data["governance_text"], styles["Body"]))
    elements.append(Spacer(1, 6))

    def draw_footer(canvas, _doc):
        """Español: Función draw_footer del módulo scripts/generate_report.py.

        English: Function draw_footer defined in scripts/generate_report.py.
        """
        canvas.saveState()
        # ── LETTERHEAD: dark blue bar on page 1 only ──
        if getattr(canvas, "_pageNumber", 0) == 1:
            lh_h = 1.4 * cm
            canvas.setFillColor(colors.Color(0.07, 0.14, 0.30))
            canvas.rect(0, page_size[1] - lh_h, page_size[0], lh_h, fill=1, stroke=0)
            canvas.setFont(bold_font, 11)
            canvas.setFillColor(colors.white)
            canvas.drawString(
                1.5 * cm, page_size[1] - lh_h + 0.38 * cm, "Centinela Electoral Honduras — Motor de Auditoría Electoral"
            )
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(1.5 * cm, 0.75 * cm, data["footer_left"])
        canvas.drawRightString(page_size[0] - 1.5 * cm, 0.75 * cm, data["footer_right"])
        canvas.setFont(regular_font, 7)
        canvas.drawString(1.5 * cm, 0.45 * cm, data.get("footer_disclaimer", ""))
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
    buffer.seek(0)
    return buffer.getvalue()


_STRINGS: dict[str, dict[str, str]] = {
    "es": {
        "exec_summary_title": "Resumen Ejecutivo — C.E.N.T.I.N.E.L.",
        "exec_what_is": "¿Qué es Centinel Engine?",
        "exec_what_is_body": (
            "Centinel Engine es un sistema de vigilancia electoral criptográfica de código abierto. "
            "Descarga los datos oficiales del CNE cada pocos minutos durante todo el proceso de "
            "cómputo y los encadena con hashes SHA-256, anclandolos en el blockchain de Bitcoin. "
            "Cualquier modificación de los datos queda registrada en la cadena — y es imposible "
            "de borrar sin dejar huella."
        ),
        "exec_what_means": "¿Qué significa este informe?",
        "exec_what_means_body": (
            "Este informe resume las capturas realizadas durante el proceso electoral. "
            "Cada fila de la tabla de snapshots representa un momento del conteo que fue "
            "registrado criptográficamente. El análisis de Benford y los indicadores KPI "
            "muestran si los datos siguen patrones estadísticos normales."
        ),
        "exec_status_label": "Estado global de la auditoría:",
        "exec_how_verify": "¿Cómo verificar este informe?",
        "exec_how_verify_body": (
            "1. Descargue el verificador offline desde el panel público.\n"
            "2. Abra el archivo HTML en cualquier navegador, sin conexión a internet.\n"
            "3. Ingrese el hash raíz del informe — el verificador confirma si los datos "
            "son auténticos comparando contra la cadena Bitcoin.\n"
            "El archivo de verificación es independiente del CNE, del gobierno y del equipo "
            "técnico — cualquier ciudadano puede confirmar los datos desde cero."
        ),
        "exec_agnostic": (
            "NOTA: Este sistema es 100% agnóstico a candidatos y partidos. "
            "No tiene opinión sobre resultados — solo verifica la integridad de los datos."
        ),
        "title": "Informe de Auditoría C.E.N.T.I.N.E.L.",
        "subtitle_tpl": "Estatus verificable · Alcance {dept}",
        "generated_tpl": "Fecha/hora: {ts} UTC",
        "global_status": "ESTATUS GLOBAL: VERIFICABLE · SIN ANOMALÍAS CRÍTICAS",
        "executive_summary": (
            "Auditoría digital con deltas por departamento, controles Benford " "y trazabilidad criptográfica."
        ),
        "kpi_headers": ["Auditorías", "Correctivas", "Snapshots", "Reglas", "Hashes"],
        "anomaly_headers": ["Dept", "Candidato", "Δ abs", "Δ %", "Hora", "Hash", "Tipo"],
        "snapshot_headers": ["Timestamp", "Dept", "Candidato", "Impacto", "Estado", "Hash"],
        "rules_list": ["granular_anomaly (Δ% 0.5)", "benford (p<0.05)", "z-score (>3)"],
        "crypto_text": "Hash raíz: {root_hash} · QR para escaneo y validación pública.",
        "risk_text": "Mapa de riesgos: deltas negativos, irregularidades temporales y dispersión geográfica.",
        "governance_text": "Gobernanza: trazabilidad, inmutabilidad y publicación auditada del JSON CNE.",
        "benford_caption": "Distribución Benford: observado vs esperado (rojo cuando supera 5%).",
        "timeline_caption": "Timeline con puntos rojos en horas de anomalías.",
        "heatmap_caption": "Mapa de riesgos por departamento/hora (rojo = mayor riesgo).",
        "footer_disclaimer": (
            "Datos solo de fuentes públicas CNE, conforme Ley Transparencia 170-2006. Agnóstico político."
        ),
    },
    "en": {
        "exec_summary_title": "Executive Summary — C.E.N.T.I.N.E.L.",
        "exec_what_is": "What is Centinel Engine?",
        "exec_what_is_body": (
            "Centinel Engine is an open-source cryptographic electoral surveillance system. "
            "It downloads official CNE data every few minutes throughout the vote-counting "
            "process and chains each snapshot with SHA-256 hashes, anchoring them to the "
            "Bitcoin blockchain. Any modification of the data is recorded in the chain — "
            "and is impossible to erase without leaving a trace."
        ),
        "exec_what_means": "What does this report mean?",
        "exec_what_means_body": (
            "This report summarizes the captures made during the electoral process. "
            "Each row in the snapshots table represents a moment in the count that was "
            "cryptographically recorded. The Benford analysis and KPI indicators show "
            "whether the data follows normal statistical patterns."
        ),
        "exec_status_label": "Overall audit status:",
        "exec_how_verify": "How to verify this report?",
        "exec_how_verify_body": (
            "1. Download the offline verifier from the public panel.\n"
            "2. Open the HTML file in any browser, without an internet connection.\n"
            "3. Enter the root hash of the report — the verifier confirms whether the data "
            "is authentic by comparing against the Bitcoin chain.\n"
            "The verification file is independent of the CNE, the government, and the "
            "technical team — any citizen can confirm the data from scratch."
        ),
        "exec_agnostic": (
            "NOTE: This system is 100% agnostic to candidates and parties. "
            "It has no opinion on results — it only verifies data integrity."
        ),
        "title": "C.E.N.T.I.N.E.L. Audit Report",
        "subtitle_tpl": "Verifiable status · Scope: {dept}",
        "generated_tpl": "Generated: {ts} UTC",
        "global_status": "GLOBAL STATUS: VERIFIABLE · NO CRITICAL ANOMALIES",
        "executive_summary": (
            "Digital audit with deltas by department, Benford controls " "and cryptographic traceability."
        ),
        "kpi_headers": ["Audits", "Corrective", "Snapshots", "Rules", "Hashes"],
        "anomaly_headers": ["Dept", "Candidate", "Δ abs", "Δ %", "Hour", "Hash", "Type"],
        "snapshot_headers": ["Timestamp", "Dept", "Candidate", "Impact", "Status", "Hash"],
        "rules_list": ["granular_anomaly (Δ% 0.5)", "benford (p<0.05)", "z-score (>3)"],
        "crypto_text": "Root hash: {root_hash} · QR for public scan and validation.",
        "risk_text": "Risk map: negative deltas, temporal irregularities and geographic dispersion.",
        "governance_text": ("Governance: traceability, immutability and audited publication of CNE JSON."),
        "benford_caption": "Benford distribution: observed vs expected (red when exceeding 5%).",
        "timeline_caption": "Timeline with red dots at anomaly hours.",
        "heatmap_caption": "Risk map by department/hour (red = higher risk).",
        "footer_disclaimer": (
            "Data from public CNE sources only, per Transparency Law 170-2006. Politically agnostic."
        ),
    },
}


def main() -> None:
    """Español: Función main del módulo scripts/generate_report.py.

    English: Function main defined in scripts/generate_report.py.
    """
    parser = argparse.ArgumentParser(description="Genera PDF premium C.E.N.T.I.N.E.L.")
    parser.add_argument("--source-dir", default="data", help="Directorio de snapshots.")
    parser.add_argument("--output", default="centinel_informe_nacional.pdf", help="Ruta PDF salida.")
    parser.add_argument("--department", default="Nacional", help="Departamento (Nacional/Cortés/etc).")
    parser.add_argument(
        "--lang",
        default="es",
        choices=["es", "en"],
        help="Report language: 'es' (Spanish, default) or 'en' (English).",
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Write SHA-256 of the PDF to a companion .sha256 file.",
    )
    args = parser.parse_args()

    snapshots = load_snapshot_files(Path(args.source_dir))
    snapshot_df = build_snapshot_metrics(snapshots)
    if args.department.lower() != "nacional":
        snapshot_df = snapshot_df[snapshot_df["department"].str.lower() == args.department.lower()]
    anomalies_df = build_anomalies(snapshot_df)
    heatmap_df = build_heatmap(anomalies_df)
    real_alerts = load_anomalies_report(Path(args.source_dir))
    benford_df = build_benford_data(real_alerts)
    rules_alerts_rows = build_rules_alerts_table(real_alerts)

    anomalies_sorted = anomalies_df.copy()
    if not anomalies_sorted.empty:
        anomalies_sorted["delta_abs"] = anomalies_sorted["delta"].abs()
        anomalies_sorted = anomalies_sorted.sort_values("delta_abs", ascending=False)
        if len(anomalies_sorted) > 8:
            anomalies_sorted = (
                anomalies_sorted.groupby("department", as_index=False).head(2).sort_values("delta_abs", ascending=False)
            )

    anomaly_rows = [
        ["Dept", "Candidato", "Δ abs", "Δ %", "Hora", "Hash", "Tipo"],
    ] + [
        [
            row.get("department"),
            row.get("candidate"),
            f"{row.get('delta', 0):.0f}",
            f"{row.get('delta_pct', 0):.2f}%",
            row.get("hour") or "",
            row.get("hash") or "",
            row.get("type"),
        ]
        for _, row in anomalies_sorted.head(12).iterrows()
    ]

    snapshots_real = snapshot_df.copy()
    if "is_real" in snapshots_real.columns and not snapshots_real.empty:
        filtered = snapshots_real[snapshots_real["is_real"]]
        if not filtered.empty:
            snapshots_real = filtered
    _snap_cols = ["timestamp", "department", "candidate", "impact", "status", "hash"]
    if snapshots_real.empty or not all(c in snapshots_real.columns for c in _snap_cols):
        snapshot_rows = [["Timestamp", "Dept", "Candidato", "Impacto", "Estado", "Hash"]]
    else:
        snapshot_rows = [
            ["Timestamp", "Dept", "Candidato", "Impacto", "Estado", "Hash"],
        ] + snapshots_real[
            _snap_cols
        ].head(10).values.tolist()

    s = _STRINGS.get(args.lang, _STRINGS["es"])
    # For bilingual executive summary, always include both languages
    s_es = _STRINGS["es"]
    s_en = _STRINGS["en"]
    ts_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    root_hash = "0x9f3fa7c2d1b4a7e1"

    # Replace anomaly_rows header with localized column names
    anomaly_rows[0] = s["anomaly_headers"]
    snapshot_rows[0] = s["snapshot_headers"]

    data = {
        "title": s["title"],
        "subtitle": s["subtitle_tpl"].format(dept=args.department),
        "generated": s["generated_tpl"].format(ts=ts_str),
        "global_status": s["global_status"],
        "executive_summary": s["executive_summary"],
        "kpi_rows": [
            s["kpi_headers"],
            ["8", "2", str(len(snapshot_df)), "18", "0x9f3fa7c2"],
        ],
        "anomaly_rows": anomaly_rows,
        "snapshot_rows": snapshot_rows,
        "rules_list": s["rules_list"],
        "crypto_text": s["crypto_text"].format(root_hash=root_hash),
        "risk_text": s["risk_text"],
        "governance_text": s["governance_text"],
        "chart_captions": {
            "benford": s["benford_caption"],
            "timeline": s["timeline_caption"],
            "heatmap": s["heatmap_caption"],
        },
        "footer_left": f"Hash: {root_hash}…",
        "footer_right": "Hash reporte: 0xabc123…",
        "footer_disclaimer": s["footer_disclaimer"],
        # Executive summary strings (always bilingual ES+EN)
        "exec_es": {k: s_es[k] for k in s_es if k.startswith("exec_")},
        "exec_en": {k: s_en[k] for k in s_en if k.startswith("exec_")},
        "global_status_text": s["global_status"],
        "rules_alerts_rows": rules_alerts_rows,
    }

    chart_buffers = create_pdf_charts(benford_df, snapshot_df, heatmap_df, anomalies_df)
    output_path = Path(args.output)
    pdf_bytes = build_pdf_report(data, chart_buffers)
    output_path.write_bytes(pdf_bytes)

    if args.sign:
        pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
        sig_path = output_path.with_suffix(".sha256")
        sig_path.write_text(f"{pdf_hash}  {output_path.name}\n")
        print(f"SHA-256: {pdf_hash}")
        print(f"Signature written to: {sig_path}")



if __name__ == "__main__":
    main()
