"""
Generate a formatted Church Membership Directory PDF.

Produces a professional directory with:
- Church header with logo
- Date/time footer on every page
- Page numbers
- Member cards with thumbnail photo placeholder, name, contact info
- Grouped by household
"""

import frappe
from datetime import datetime
import os
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black, lightgrey
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# ── Church Colors ──────────────────────────────────────────────
MINT = HexColor("#4ABFAB")
MINT_DARK = HexColor("#3a9e8a")
LIGHT_BLUE = HexColor("#6BB8D4")
LIGHT_GREY = HexColor("#F4F6F8")
BLUE_TINT = HexColor("#EBF6FA")
TEXT_DARK = HexColor("#2C3E50")
TEXT_MED = HexColor("#5A6C7D")
TEXT_LIGHT = HexColor("#8899AA")


class DirectoryTemplate(SimpleDocTemplate):
    """Custom template with header and footer."""

    def __init__(self, *args, **kwargs):
        self.church_name = kwargs.pop("church_name", "Pleasant Springs Church")
        self.generated_date = kwargs.pop("generated_date", datetime.now())
        super().__init__(*args, **kwargs)

    def afterPage(self):
        """Called after each page is generated."""
        pass


def _header_footer(canvas_obj, doc):
    """Draw header and footer on every page."""
    canvas_obj.saveState()
    width, height = letter

    # ── Header ──────────────────────────────────────────────
    # Gradient bar
    canvas_obj.setFillColor(MINT_DARK)
    canvas_obj.rect(0, height - 50, width, 50, fill=1, stroke=0)

    # Church name
    canvas_obj.setFillColor(white)
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.drawCentredString(width / 2, height - 32, "Pleasant Springs Church")

    # Subtitle
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawCentredString(width / 2, height - 44, "Membership Directory")

    # ── Footer ──────────────────────────────────────────────
    canvas_obj.setFillColor(LIGHT_GREY)
    canvas_obj.rect(0, 0, width, 35, fill=1, stroke=0)

    # Thin accent line above footer
    canvas_obj.setStrokeColor(MINT)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(36, 35, width - 36, 35)

    # Date & time - left
    canvas_obj.setFillColor(TEXT_LIGHT)
    canvas_obj.setFont("Helvetica", 8)
    now = datetime.now()
    canvas_obj.drawString(
        40, 14,
        f"Generated: {now.strftime('%B %d, %Y at %I:%M %p')}"
    )

    # Page number - right
    page_num = canvas_obj.getPageNumber()
    canvas_obj.drawRightString(width - 40, 14, f"Page {page_num}")

    # Center motto
    canvas_obj.setFillColor(TEXT_MED)
    canvas_obj.setFont("Helvetica-Oblique", 7)
    canvas_obj.drawCentredString(
        width / 2, 14,
        "Community \u2022 Home \u2022 Unity \u2022 Relationship \u2022 Care \u2022 Hope"
    )

    canvas_obj.restoreState()


def _build_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DirectoryTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=MINT_DARK,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="DirectorySubtitle",
        fontName="Helvetica",
        fontSize=10,
        textColor=TEXT_MED,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name="HouseholdHeader",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=MINT_DARK,
        spaceBefore=14,
        spaceAfter=6,
        leftIndent=0,
    ))

    styles.add(ParagraphStyle(
        name="MemberName",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=TEXT_DARK,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name="MemberRole",
        fontName="Helvetica-Oblique",
        fontSize=8,
        textColor=MINT,
        spaceAfter=1,
    ))

    styles.add(ParagraphStyle(
        name="MemberDetail",
        fontName="Helvetica",
        fontSize=8.5,
        textColor=TEXT_MED,
        spaceAfter=1,
        leading=11,
    ))

    styles.add(ParagraphStyle(
        name="MemberLabel",
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=TEXT_DARK,
    ))

    styles.add(ParagraphStyle(
        name="SectionNote",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=TEXT_LIGHT,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=16,
    ))

    return styles


def _get_photo_element(image_url, site_url):
    """Try to load a member photo, return placeholder if unavailable."""
    photo_size = 0.85 * inch

    if image_url:
        try:
            full_url = site_url.rstrip("/") + image_url
            img = Image(full_url, width=photo_size, height=photo_size)
            return img
        except Exception:
            pass

    # Placeholder: mint-tinted box with person icon
    return None


def _build_member_card(member, styles, site_url):
    """Build a table-based member card with photo + info."""
    photo_size = 0.85 * inch

    # ── Photo column ──────────────────────────────────────
    photo = _get_photo_element(member.get("image"), site_url)

    # ── Info column ───────────────────────────────────────
    info_parts = []

    # Name
    name_text = member.get("full_name", "Unknown")
    info_parts.append(Paragraph(name_text, styles["MemberName"]))

    # Role badge
    role = member.get("household_role", "")
    if role:
        info_parts.append(Paragraph(role, styles["MemberRole"]))

    # Details grid
    details = []
    if member.get("mobile"):
        details.append(f"<b>Phone:</b> {member['mobile']}")
    if member.get("email_address"):
        email = member["email_address"].lower()
        details.append(f"<b>Email:</b> {email}")
    if member.get("date_of_birth"):
        dob = _format_date(member["date_of_birth"])
        details.append(f"<b>Born:</b> {dob}")
    if member.get("baptism_date"):
        bap = _format_date(member["baptism_date"])
        details.append(f"<b>Baptized:</b> {bap}")
    if member.get("wedding_anniversary"):
        ann = _format_date(member["wedding_anniversary"])
        details.append(f"<b>Anniversary:</b> {ann}")
    if member.get("membership_type"):
        details.append(f"<b>Type:</b> {member['membership_type']}")
    if member.get("member_since"):
        ms = _format_date(member["member_since"])
        details.append(f"<b>Member Since:</b> {ms}")

    for d in details:
        info_parts.append(Paragraph(d, styles["MemberDetail"]))

    # ── Build card table ──────────────────────────────────
    if photo:
        card_data = [[photo, info_parts]]
        col_widths = [photo_size + 12, None]
    else:
        # Placeholder box drawn via table style
        placeholder_text = Paragraph(
            f"<font size='18' color='#4ABFAB'>\u263A</font>",
            ParagraphStyle("ph", alignment=TA_CENTER, spaceBefore=18)
        )
        card_data = [[placeholder_text, info_parts]]
        col_widths = [photo_size + 12, None]

    card_table = Table(card_data, colWidths=col_widths, hAlign="LEFT")
    card_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 4),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        # Photo cell background
        ("BACKGROUND", (0, 0), (0, 0), BLUE_TINT),
        ("BOX", (0, 0), (0, 0), 0.5, MINT),
    ]))

    return card_table


def _format_date(date_str):
    """Format a date string nicely."""
    if not date_str:
        return ""
    try:
        if isinstance(date_str, str):
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            dt = date_str
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return str(date_str)


@frappe.whitelist()
def generate_directory_pdf():
    """Generate the membership directory PDF and return it for download."""
    site_url = frappe.utils.get_url()

    # Fetch all active members ordered by household
    members = frappe.get_all(
        "Church Member",
        filters={"is_deceased": 0},
        fields=[
            "name", "first_name", "last_name", "full_name", "gender",
            "date_of_birth", "image", "member_id", "member_since",
            "membership_type", "membership_status", "baptism_date",
            "wedding_anniversary", "household_name", "household_role",
            "email_address", "mobile", "is_deceased"
        ],
        order_by="household_name asc, field(household_role, 'Head', 'Spouse', 'Child', 'Other') asc, full_name asc",
    )

    styles = _build_styles()
    story = []

    # ── Title Page Content ────────────────────────────────
    story.append(Spacer(1, 0.8 * inch))
    story.append(Paragraph("Membership Directory", styles["DirectoryTitle"]))
    story.append(Paragraph(
        f"Henderson / Pinson, Tennessee  \u2022  {len(members)} Active Members  \u2022  {datetime.now().strftime('%B %Y')}",
        styles["DirectorySubtitle"],
    ))
    story.append(HRFlowable(
        width="60%", thickness=1.5, color=MINT,
        spaceAfter=16, spaceBefore=4, hAlign="CENTER"
    ))
    story.append(Paragraph(
        "For church use only. Please do not distribute without permission.",
        styles["SectionNote"],
    ))

    # ── Member Cards Grouped by Household ─────────────────
    current_household = None

    for member in members:
        hh = member.get("household_name", "Other")

        if hh != current_household:
            current_household = hh

            # Household header with accent bar
            story.append(Spacer(1, 6))
            story.append(HRFlowable(
                width="100%", thickness=0.75, color=LIGHT_BLUE,
                spaceAfter=2, spaceBefore=8, hAlign="LEFT"
            ))
            story.append(Paragraph(
                f"\u25B6  {hh} Household",
                styles["HouseholdHeader"]
            ))

        # Member card
        card = _build_member_card(member, styles, site_url)
        story.append(card)
        story.append(Spacer(1, 6))

    # ── Footer note ───────────────────────────────────────
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(
        width="80%", thickness=1, color=MINT,
        spaceAfter=8, spaceBefore=12, hAlign="CENTER"
    ))
    story.append(Paragraph(
        "End of Directory  \u2022  Pleasant Springs Church  \u2022  " +
        datetime.now().strftime("%B %d, %Y"),
        styles["SectionNote"],
    ))

    # ── Build PDF ─────────────────────────────────────────
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=70,       # Space for header
        bottomMargin=50,    # Space for footer
        leftMargin=36,
        rightMargin=36,
        title="Pleasant Springs Church - Membership Directory",
        author="Pleasant Springs Church",
    )

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)

    # Return as downloadable file
    pdf_content = buffer.getvalue()
    buffer.close()

    frappe.local.response.filename = f"Membership_Directory_{datetime.now().strftime('%Y%m%d')}.pdf"
    frappe.local.response.filecontent = pdf_content
    frappe.local.response.type = "download"
    frappe.local.response.content_type = "application/pdf"
