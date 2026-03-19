"""
Generate a formatted Church Membership Directory PDF.

Uses Frappe's built-in HTML-to-PDF (wkhtmltopdf) — no external dependencies.
Produces a professional directory with:
- Church-branded header on every page
- Date/time footer with page numbers
- Member cards with thumbnail photo spot, name, contact info
- Grouped by household
"""

import frappe
from frappe.utils.pdf import get_pdf
from datetime import datetime


def _format_date(date_val):
    """Format a date value nicely."""
    if not date_val:
        return ""
    try:
        if isinstance(date_val, str):
            dt = datetime.strptime(date_val, "%Y-%m-%d")
        else:
            dt = date_val
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return str(date_val)


def _build_member_html(member, site_url):
    """Build HTML for a single member card."""
    photo_html = ""
    if member.get("image"):
        photo_url = site_url.rstrip("/") + member["image"]
        photo_html = f'<img src="{photo_url}" style="width:65px;height:65px;object-fit:cover;border-radius:6px;border:2px solid #4ABFAB;" />'
    else:
        # Placeholder with initials
        first = (member.get("first_name") or "?")[0].upper()
        last = (member.get("last_name") or "?")[0].upper()
        photo_html = f'''<div style="width:65px;height:65px;border-radius:6px;background:linear-gradient(135deg,#EBF6FA,#d4eff7);
            border:2px solid #6BB8D4;display:flex;align-items:center;justify-content:center;">
            <span style="font-size:22px;font-weight:bold;color:#4ABFAB;">{first}{last}</span>
        </div>'''

    # Details
    details = []
    if member.get("mobile"):
        details.append(f'<span style="color:#5A6C7D;font-size:9px;"><b>Phone:</b> {member["mobile"]}</span>')
    if member.get("email_address"):
        email = member["email_address"].lower()
        details.append(f'<span style="color:#5A6C7D;font-size:9px;"><b>Email:</b> {email}</span>')
    if member.get("date_of_birth"):
        details.append(f'<span style="color:#5A6C7D;font-size:9px;"><b>Born:</b> {_format_date(member["date_of_birth"])}</span>')
    if member.get("baptism_date"):
        details.append(f'<span style="color:#5A6C7D;font-size:9px;"><b>Baptized:</b> {_format_date(member["baptism_date"])}</span>')
    if member.get("wedding_anniversary"):
        details.append(f'<span style="color:#5A6C7D;font-size:9px;"><b>Anniversary:</b> {_format_date(member["wedding_anniversary"])}</span>')
    if member.get("membership_type"):
        details.append(f'<span style="color:#5A6C7D;font-size:9px;"><b>Type:</b> {member["membership_type"]}</span>')
    if member.get("member_since"):
        details.append(f'<span style="color:#5A6C7D;font-size:9px;"><b>Since:</b> {_format_date(member["member_since"])}</span>')

    details_html = "<br/>".join(details)

    role = member.get("household_role", "")
    role_html = f'<div style="color:#4ABFAB;font-size:8px;font-style:italic;margin-bottom:2px;">{role}</div>' if role else ""

    return f'''
    <tr>
        <td style="width:80px;padding:6px 8px 6px 4px;vertical-align:top;">{photo_html}</td>
        <td style="padding:6px 4px;vertical-align:top;">
            <div style="font-size:12px;font-weight:bold;color:#2C3E50;margin-bottom:1px;">{member.get("full_name", "Unknown")}</div>
            {role_html}
            {details_html}
        </td>
    </tr>'''


@frappe.whitelist()
def generate_directory_pdf():
    """Generate the membership directory PDF and return it for download."""
    site_url = frappe.utils.get_url()
    now = datetime.now()

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
        order_by="household_name asc, full_name asc",
    )

    # Group by household
    households = {}
    for m in members:
        hh = m.get("household_name") or "Other"
        if hh not in households:
            households[hh] = []
        households[hh].append(m)

    # Build member cards HTML
    body_html = ""
    for hh_name in sorted(households.keys()):
        hh_members = households[hh_name]
        # Sort: Head first, then Spouse, then Child, then Other
        role_order = {"Head": 0, "Spouse": 1, "Child": 2, "Other": 3}
        hh_members.sort(key=lambda m: (role_order.get(m.get("household_role", "Other"), 3), m.get("full_name", "")))

        body_html += f'''
        <div style="margin-bottom:4px;margin-top:12px;">
            <div style="border-bottom:2px solid #6BB8D4;padding-bottom:2px;margin-bottom:4px;">
                <span style="font-size:13px;font-weight:bold;color:#3a9e8a;">&#9654; {hh_name} Household</span>
            </div>
            <table style="width:100%;border-collapse:collapse;">'''

        for member in hh_members:
            body_html += _build_member_html(member, site_url)

        body_html += "</table></div>"

    # Full HTML document
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: Letter;
                margin: 0.5in 0.4in 0.7in 0.4in;

                @top-center {{
                    content: "";
                }}
                @bottom-left {{
                    content: "Generated: {now.strftime('%B %d, %Y at %I:%M %p')}";
                    font-size: 7px;
                    color: #8899AA;
                    font-family: Arial, sans-serif;
                }}
                @bottom-center {{
                    content: "Community \\2022  Home \\2022  Unity \\2022  Relationship \\2022  Care \\2022  Hope";
                    font-size: 6px;
                    color: #5A6C7D;
                    font-style: italic;
                    font-family: Arial, sans-serif;
                }}
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 7px;
                    color: #8899AA;
                    font-family: Arial, sans-serif;
                }}
            }}

            body {{
                font-family: Arial, Helvetica, sans-serif;
                color: #2C3E50;
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <!-- Header Banner -->
        <div style="background:linear-gradient(135deg, #3a9e8a, #4ABFAB, #6BB8D4);
                     padding:14px 20px;margin:-10px -10px 10px -10px;border-radius:0 0 8px 8px;text-align:center;">
            <div style="font-size:20px;font-weight:bold;color:white;letter-spacing:1px;">Pleasant Springs Church</div>
            <div style="font-size:9px;color:rgba(255,255,255,0.85);margin-top:2px;">Membership Directory</div>
        </div>

        <!-- Title Block -->
        <div style="text-align:center;margin:16px 0 8px 0;">
            <div style="font-size:20px;font-weight:bold;color:#3a9e8a;">Membership Directory</div>
            <div style="font-size:10px;color:#5A6C7D;margin-top:4px;">
                Henderson / Pinson, Tennessee &bull; {len(members)} Active Members &bull; {now.strftime('%B %Y')}
            </div>
            <div style="width:60%;margin:8px auto;border-top:2px solid #4ABFAB;"></div>
            <div style="font-size:8px;color:#8899AA;font-style:italic;">
                For church use only. Please do not distribute without permission.
            </div>
        </div>

        <!-- Member Directory -->
        {body_html}

        <!-- Footer -->
        <div style="text-align:center;margin-top:20px;padding-top:10px;border-top:1.5px solid #4ABFAB;">
            <span style="font-size:9px;color:#8899AA;font-style:italic;">
                End of Directory &bull; Pleasant Springs Church &bull; {now.strftime('%B %d, %Y')}
            </span>
        </div>
    </body>
    </html>'''

    # Generate PDF using Frappe's built-in wkhtmltopdf
    pdf_options = {
        "page-size": "Letter",
        "margin-top": "12mm",
        "margin-bottom": "18mm",
        "margin-left": "10mm",
        "margin-right": "10mm",
        "header-spacing": "5",
        "footer-spacing": "5",
        "footer-font-size": "7",
        "footer-left": f"Generated: {now.strftime('%B %d, %Y at %I:%M %p')}",
        "footer-center": "Community - Home - Unity - Relationship - Care - Hope",
        "footer-right": "Page [page] of [topage]",
        "footer-line": "",
        "encoding": "UTF-8",
        "no-outline": "",
        "print-media-type": "",
    }

    pdf_content = get_pdf(html, options=pdf_options)

    frappe.local.response.filename = f"Membership_Directory_{now.strftime('%Y%m%d')}.pdf"
    frappe.local.response.filecontent = pdf_content
    frappe.local.response.type = "download"
    frappe.local.response.content_type = "application/pdf"
