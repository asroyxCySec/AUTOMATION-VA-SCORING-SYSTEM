from __future__ import annotations

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app import config
from app.services.assessment_service import AssessmentView
from app.services.settings_service import AppSettings
from app.utils.helpers import report_basename

_PRIMARY = colors.HexColor("#13213F")
_ACCENT = colors.HexColor("#2D6CDF")
_TEXT_DARK = colors.HexColor("#1B1F2A")
_TEXT_MUTED = colors.HexColor("#555C6B")
_HEADER_FILL = colors.HexColor("#13213F")
_LABEL_FILL = colors.HexColor("#E5EAF6")
_ZEBRA_FILL = colors.HexColor("#F1F4FB")
_BORDER = colors.HexColor("#C7D0E4")
_WHITE = colors.white

_SEVERITY_FILL = {
    "Critical": colors.HexColor("#C0182B"),
    "High": colors.HexColor("#E0561B"),
    "Medium": colors.HexColor("#C9911C"),
    "Low": colors.HexColor("#2E8B57"),
    "Informational": colors.HexColor("#2D6CDF"),
}

_CONTENT_WIDTH = A4[0] - 4 * cm


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_institution": ParagraphStyle(
            "cover_institution", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=16, textColor=_PRIMARY, alignment=TA_CENTER, leading=20,
        ),
        "cover_address": ParagraphStyle(
            "cover_address", parent=base["Normal"], fontName="Helvetica",
            fontSize=10, textColor=_TEXT_MUTED, alignment=TA_CENTER, leading=14,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=26, textColor=_ACCENT, alignment=TA_CENTER, leading=30,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Normal"], fontName="Helvetica",
            fontSize=12, textColor=_TEXT_MUTED, alignment=TA_CENTER, leading=16,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=12, textColor=_WHITE, alignment=TA_LEFT, leading=15,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9.5, textColor=_PRIMARY, alignment=TA_LEFT, leading=13,
        ),
        "value": ParagraphStyle(
            "value", parent=base["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=_TEXT_DARK, alignment=TA_LEFT, leading=13,
        ),
        "header_cell": ParagraphStyle(
            "header_cell", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9.5, textColor=_WHITE, alignment=TA_LEFT, leading=13,
        ),
        "header_cell_center": ParagraphStyle(
            "header_cell_center", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9.5, textColor=_WHITE, alignment=TA_CENTER, leading=13,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=_TEXT_DARK, alignment=TA_LEFT, leading=13,
        ),
        "cell_center": ParagraphStyle(
            "cell_center", parent=base["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=_TEXT_DARK, alignment=TA_CENTER, leading=13,
        ),
        "badge": ParagraphStyle(
            "badge", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=15, textColor=_WHITE, alignment=TA_CENTER, leading=19,
        ),
        "note": ParagraphStyle(
            "note", parent=base["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=_TEXT_MUTED, alignment=TA_LEFT, leading=14,
        ),
        "meta_label": ParagraphStyle(
            "meta_label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=10, textColor=_PRIMARY, alignment=TA_LEFT, leading=14,
        ),
        "meta_value": ParagraphStyle(
            "meta_value", parent=base["Normal"], fontName="Helvetica",
            fontSize=10, textColor=_TEXT_DARK, alignment=TA_LEFT, leading=14,
        ),
    }


class _ReportDoc(BaseDocTemplate):
    def __init__(self, path: str, settings: AppSettings) -> None:
        super().__init__(
            path, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
            title="Vulnerability Assessment Report", author=config.APP_NAME,
        )
        self._settings = settings
        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height, id="main",
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates(
            [
                PageTemplate(id="cover", frames=[frame], onPage=self._decorate_cover),
                PageTemplate(id="body", frames=[frame], onPage=self._decorate_body),
            ]
        )

    def _decorate_cover(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFillColor(_ACCENT)
        canvas.rect(0, A4[1] - 0.5 * cm, A4[0], 0.5 * cm, stroke=0, fill=1)
        canvas.setFillColor(_PRIMARY)
        canvas.rect(0, 0, A4[0], 0.5 * cm, stroke=0, fill=1)
        canvas.restoreState()

    def _decorate_body(self, canvas, doc) -> None:
        canvas.saveState()
        header_text = self._settings.report_header or "VULNERABILITY ASSESSMENT REPORT"
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(_TEXT_MUTED)
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.35 * cm, header_text)
        canvas.setStrokeColor(_BORDER)
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, A4[1] - 1.55 * cm, A4[0] - 2 * cm, A4[1] - 1.55 * cm)
        footer_label = self._settings.report_footer or (
            f"{self._settings.institution_name} | {config.APP_NAME} v{config.APP_VERSION}"
        )
        canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(2 * cm, 1.25 * cm, footer_label)
        canvas.drawRightString(A4[0] - 2 * cm, 1.25 * cm, f"Halaman {doc.page - 1}")
        canvas.restoreState()


def _section(title: str, style: ParagraphStyle) -> Table:
    table = Table([[Paragraph(title.upper(), style)]], colWidths=[_CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _HEADER_FILL),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def _key_value(rows: list[tuple[str, str]], styles: dict[str, ParagraphStyle]) -> Table:
    label_width = 5.4 * cm
    value_width = _CONTENT_WIDTH - label_width
    data = [
        [Paragraph(label, styles["label"]), Paragraph(value if value else "-", styles["value"])]
        for label, value in rows
    ]
    table = Table(data, colWidths=[label_width, value_width])
    style = [
        ("BACKGROUND", (0, 0), (0, -1), _LABEL_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for index in range(len(rows)):
        if index % 2 == 1:
            style.append(("BACKGROUND", (1, index), (1, index), _ZEBRA_FILL))
    table.setStyle(TableStyle(style))
    return table


def _matrix(headers: list[str], rows: list[list[str]], widths: list[float], styles: dict[str, ParagraphStyle]) -> Table:
    head = [Paragraph(headers[0], styles["header_cell_center"])] + [
        Paragraph(text, styles["header_cell"]) for text in headers[1:]
    ]
    data = [head]
    for row in rows:
        cells = [Paragraph(row[0], styles["cell_center"])] + [
            Paragraph(text, styles["cell"]) for text in row[1:]
        ]
        data.append(cells)
    table = Table(data, colWidths=[w * cm for w in widths])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for index in range(1, len(rows) + 1):
        if index % 2 == 0:
            style.append(("BACKGROUND", (0, index), (-1, index), _ZEBRA_FILL))
    table.setStyle(TableStyle(style))
    return table


def _bullets(title: str, items: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    data = [[Paragraph(title, styles["header_cell"])]]
    for index, item in enumerate(items, start=1):
        data.append([Paragraph(f"{index}.&nbsp;&nbsp;{item}", styles["cell"])])
    table = Table(data, colWidths=[_CONTENT_WIDTH])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _ACCENT),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for index in range(1, len(items) + 1):
        if index % 2 == 0:
            style.append(("BACKGROUND", (0, index), (-1, index), _ZEBRA_FILL))
    table.setStyle(TableStyle(style))
    return table


def _badge(view: AssessmentView, styles: dict[str, ParagraphStyle]) -> Table:
    fill = _SEVERITY_FILL.get(view.final_severity, _ACCENT)
    text = f"{view.final_severity.upper()}  |  CVSS {view.cvss_score:.1f}"
    table = Table([[Paragraph(text, styles["badge"])]], colWidths=[9 * cm])
    table.hAlign = "CENTER"
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fill),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return table


def _build_cover_flow(view: AssessmentView, settings: AppSettings, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = [Spacer(1, 1.4 * cm)]
    if settings.report_logo_path and os.path.isfile(settings.report_logo_path):
        try:
            logo = Image(settings.report_logo_path)
            ratio = logo.imageHeight / float(logo.imageWidth or 1)
            logo.drawWidth = 3.6 * cm
            logo.drawHeight = 3.6 * cm * ratio
            logo.hAlign = "CENTER"
            flow.append(logo)
            flow.append(Spacer(1, 0.4 * cm))
        except (OSError, ValueError):
            pass
    flow.append(Paragraph(settings.institution_name or config.APP_NAME, styles["cover_institution"]))
    if settings.institution_address:
        flow.append(Paragraph(settings.institution_address, styles["cover_address"]))
    flow.append(Spacer(1, 1.6 * cm))
    flow.append(Paragraph(settings.report_header or "VULNERABILITY ASSESSMENT REPORT", styles["cover_title"]))
    flow.append(Spacer(1, 0.2 * cm))
    flow.append(Paragraph("Laporan Penilaian Akhir Kerentanan", styles["cover_subtitle"]))
    flow.append(Spacer(1, 0.9 * cm))
    flow.append(_badge(view, styles))
    flow.append(Spacer(1, 1.6 * cm))
    meta = [
        ("Target / URL", view.target),
        ("Nama Temuan", view.finding_name),
        ("Tanggal Ditemukan", view.found_on.strftime("%d %B %Y")),
        ("Peneliti / Handle", view.researcher),
        ("Tanggal Laporan", datetime.now().strftime("%d %B %Y")),
    ]
    meta_table = Table(
        [[Paragraph(label, styles["meta_label"]), Paragraph(value or "-", styles["meta_value"])] for label, value in meta],
        colWidths=[5.0 * cm, _CONTENT_WIDTH - 5.0 * cm],
    )
    meta_style = [
        ("BACKGROUND", (0, 0), (0, -1), _LABEL_FILL),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    for index in range(len(meta)):
        if index % 2 == 1:
            meta_style.append(("BACKGROUND", (1, index), (1, index), _ZEBRA_FILL))
    meta_table.setStyle(TableStyle(meta_style))
    flow.append(meta_table)
    return flow


def _build_body_flow(view: AssessmentView, settings: AppSettings, styles: dict[str, ParagraphStyle]) -> list:
    gap = Spacer(1, 0.45 * cm)
    flow: list = []

    flow.append(_section("Informasi Temuan", styles["section"]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(
        _key_value(
            [
                ("Target / URL", view.target),
                ("Nama Temuan", view.finding_name),
                ("Tanggal Ditemukan", view.found_on.strftime("%d %B %Y")),
                ("Peneliti / Handle", view.researcher),
                ("Pemilik Penilaian", view.owner_username),
            ],
            styles,
        )
    )
    flow.append(gap)

    flow.append(_section("CVSS Scoring", styles["section"]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(
        _key_value(
            [
                ("Vector String", view.cvss_vector),
                ("Base Score", f"{view.cvss_score:.1f}"),
                ("Severity Awal", view.base_severity),
                ("Severity Akhir", view.final_severity),
                ("Severity Upgrade", "Ya" if view.severity_upgraded else "Tidak"),
            ],
            styles,
        )
    )
    flow.append(gap)

    flow.append(_section("Parameter Detail", styles["section"]))
    flow.append(Spacer(1, 0.15 * cm))
    parameter_rows = [
        [view.metric_codes["AV"], view.parameter_labels.get("Attack Vector", "-"), "Attack Vector"],
        [view.metric_codes["AC"], view.parameter_labels.get("Attack Complexity", "-"), "Attack Complexity"],
        [view.metric_codes["PR"], view.parameter_labels.get("Privileges Required", "-"), "Privileges Required"],
        [view.metric_codes["UI"], view.parameter_labels.get("User Interaction", "-"), "User Interaction"],
        [view.metric_codes["S"], view.parameter_labels.get("Scope", "-"), "Scope"],
        [view.metric_codes["C"], view.parameter_labels.get("Confidentiality Impact", "-"), "Confidentiality Impact"],
        [view.metric_codes["I"], view.parameter_labels.get("Integrity Impact", "-"), "Integrity Impact"],
        [view.metric_codes["A"], view.parameter_labels.get("Availability Impact", "-"), "Availability Impact"],
    ]
    flow.append(_matrix(["Kode", "Nilai", "Parameter"], parameter_rows, [2.6, 6.0, 8.4], styles))
    flow.append(gap)

    flow.append(_section("Exploitability", styles["section"]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(
        _key_value(
            [
                ("Public Exploit / CVE", "Ya" if view.public_exploit else "Tidak"),
                ("CVE ID", view.cve_id or "-"),
                ("Reproducible", "Ya" if view.reproducible else "Tidak"),
                ("Proof of Concept", "Tersedia" if view.poc_available else "Tidak tersedia"),
                ("Lampiran PoC", os.path.basename(view.poc_attachment_path) if view.poc_attachment_path else "-"),
            ],
            styles,
        )
    )
    flow.append(gap)

    flow.append(_section("Impact Detail", styles["section"]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(
        _key_value(
            [
                ("Data Terdampak", view.impacted_data),
                ("Estimasi Jumlah User", view.estimated_users),
                ("Regulasi Terkait", ", ".join(view.regulations) if view.regulations else "-"),
                ("Business Impact", view.business_impact),
            ],
            styles,
        )
    )
    flow.append(gap)

    flow.append(_section("Rekomendasi Remediation", styles["section"]))
    flow.append(Spacer(1, 0.15 * cm))
    flow.append(_bullets(f"Langkah Teknis - {view.remediation_name}", list(view.remediation_steps), styles))
    flow.append(Spacer(1, 0.2 * cm))
    flow.append(
        _key_value(
            [
                ("Referensi OWASP", view.remediation_owasp),
                ("CWE", view.remediation_cwe),
                ("CAPEC", view.remediation_capec),
                ("Target Deadline", view.deadline_label),
            ],
            styles,
        )
    )
    if view.remediation_references:
        flow.append(Spacer(1, 0.2 * cm))
        flow.append(_bullets("Referensi Tambahan", list(view.remediation_references), styles))
    flow.append(gap)

    flow.append(_section("Catatan Severity Chaining", styles["section"]))
    flow.append(Spacer(1, 0.15 * cm))
    if view.severity_upgraded and view.severity_reasons:
        flow.append(_bullets("Alasan Peningkatan Severity", list(view.severity_reasons), styles))
    else:
        flow.append(
            Paragraph(
                "Tidak ditemukan kombinasi kondisi yang memicu peningkatan severity. "
                "Severity akhir setara dengan hasil perhitungan CVSS dasar.",
                styles["note"],
            )
        )
    return flow


def export_pdf(view: AssessmentView, settings: AppSettings, output_dir: str | None = None) -> str:
    config.ensure_directories()
    target_dir = output_dir or str(config.EXPORT_DIR)
    os.makedirs(target_dir, exist_ok=True)

    basename = report_basename(view.target, view.finding_name, view.found_on)
    output_path = os.path.join(target_dir, f"{basename}.pdf")

    styles = _styles()
    doc = _ReportDoc(output_path, settings)
    story: list = [NextPageTemplate("body")]
    story.extend(_build_cover_flow(view, settings, styles))
    story.append(PageBreak())
    story.extend(_build_body_flow(view, settings, styles))
    doc.build(story)
    return output_path
