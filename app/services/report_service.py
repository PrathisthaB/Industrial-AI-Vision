"""
Report service — generates professional incident reports for violations and
supports exporting them as PDF or CSV.

PDF generation uses reportlab (pure-Python, no external binary dependency) so
the platform can produce documents in any deployment environment.
"""

import csv
import io
import uuid
from datetime import datetime
from pathlib import Path

from app.models import IncidentReport, Violation

RECOMMENDED_ACTIONS = {
    "missing_helmet": "Immediately halt worker activity and issue an approved hard hat before re-entry to the zone.",
    "missing_vest": "Provide a high-visibility vest and confirm compliance before the worker resumes duties.",
    "missing_boots": "Issue certified safety footwear; restrict access to the floor until compliant.",
}

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _incident_code():
    return f"INC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def generate_report_for_violation(violation_id, reports_dir):
    """Create (and persist) an incident report record for one violation."""
    violation = Violation.get(violation_id)
    if violation is None:
        raise ValueError(f"Violation {violation_id} not found")

    incident_code = _incident_code()
    recommended_action = RECOMMENDED_ACTIONS.get(
        violation["violation_type"],
        "Review the evidence screenshot and enforce site PPE policy immediately.",
    )

    report_id = IncidentReport.create(
        incident_code=incident_code,
        violation_id=violation_id,
        severity=violation["severity"],
        recommended_action=recommended_action,
    )

    report = IncidentReport.get(report_id)

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_path / f"{incident_code}.pdf"
    build_pdf_report(report, pdf_path)
    IncidentReport.set_file_path(report_id, f"{incident_code}.pdf")
    report["file_path"] = f"{incident_code}.pdf"

    return report


def build_pdf_report(report, output_path):
    """Render a single-incident PDF using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "IncidentTitle", parent=styles["Heading1"], textColor=colors.HexColor("#0f172a")
    )
    body_style = styles["BodyText"]

    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                             topMargin=20 * mm, bottomMargin=20 * mm)
    elements = [
        Paragraph("AI-Powered Industrial Safety Monitoring Platform", styles["Heading3"]),
        Paragraph("Incident Report", title_style),
        Spacer(1, 6),
    ]

    data = [
        ["Incident ID", report["incident_code"]],
        ["Time", report["violation_time"]],
        ["Violation", report["violation_type"].replace("_", " ").title()],
        ["Severity", report["severity"].upper()],
        ["Confidence", f"{report['confidence'] * 100:.1f}%"],
        ["Recommended Action", report["recommended_action"]],
    ]
    table = Table(data, colWidths=[130, 340])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    screenshot_path = report.get("screenshot_path")
    if screenshot_path:
        full_path = Path(screenshot_path)
        if not full_path.is_absolute():
            full_path = Path.cwd() / screenshot_path
        if full_path.exists():
            elements.append(Paragraph("Evidence", styles["Heading4"]))
            elements.append(RLImage(str(full_path), width=400, height=240))

    elements.append(Spacer(1, 16))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by the automated "
        f"compliance monitoring pipeline. This report is for internal EHS review.",
        styles["BodyText"],
    ))

    doc.build(elements)
    return output_path


def export_violations_csv(violations):
    """Return CSV text (in-memory) for a list of violation dict rows."""
    buffer = io.StringIO()
    fieldnames = [
        "id", "timestamp", "violation_type", "severity",
        "confidence", "compliance_score", "camera_id", "status", "screenshot_path",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for v in violations:
        writer.writerow(v)
    return buffer.getvalue()


def sort_by_severity(reports):
    return sorted(reports, key=lambda r: SEVERITY_ORDER.get(r["severity"], 0), reverse=True)
