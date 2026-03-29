import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    create_church_member_custom_fields()
    create_default_cemetery()
    create_default_monument_types()
    create_default_fee_types()
    create_cemetery_manager_role()
    create_workspace_sidebar()
    create_desktop_icon()


def create_church_member_custom_fields():
    custom_fields = {
        "Church Member": [
            dict(
                fieldname="cemetery_section_break",
                fieldtype="Section Break",
                label="Cemetery",
                insert_after="deceased_date",
                module="Cemetery Management",
                depends_on="eval:doc.is_deceased",
                collapsible=1,
            ),
            dict(
                fieldname="burial_record",
                fieldtype="Link",
                label="Burial Record",
                options="Burial Record",
                insert_after="cemetery_section_break",
                module="Cemetery Management",
                depends_on="eval:doc.is_deceased",
            ),
            dict(
                fieldname="burial_plot",
                fieldtype="Link",
                label="Burial Plot",
                options="Burial Plot",
                insert_after="burial_record",
                module="Cemetery Management",
                depends_on="eval:doc.is_deceased",
                read_only=1,
            ),
        ]
    }
    create_custom_fields(custom_fields, update=True)


def create_default_cemetery():
    if not frappe.db.exists("Cemetery", "Pleasant Springs Cemetery"):
        doc = frappe.new_doc("Cemetery")
        doc.cemetery_name = "Pleasant Springs Cemetery"
        doc.status = "Active"
        doc.findagrave_id = "17250"
        doc.findagrave_url = "https://www.findagrave.com/cemetery/17250/pleasant-springs-cemetery"
        doc.city = "Henderson"
        doc.state = "Tennessee"
        doc.county = "Chester"
        doc.latitude = 35.418182
        doc.longitude = -88.790044
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)
    frappe.db.commit()


def create_default_monument_types():
    types = [
        {"monument_type_name": "Flat/Flush", "description": "Flat marker level with the ground"},
        {"monument_type_name": "Upright", "description": "Traditional upright headstone"},
        {"monument_type_name": "Bench", "description": "Bench-style memorial monument"},
        {"monument_type_name": "Slant", "description": "Angled slant marker on a base"},
        {"monument_type_name": "Ledger", "description": "Full-length flat stone covering the grave"},
        {"monument_type_name": "Government (VA)", "description": "Government-issued veteran headstone"},
        {"monument_type_name": "Obelisk", "description": "Tall pointed pillar monument"},
        {"monument_type_name": "Cross", "description": "Cross-shaped monument"},
    ]
    for t in types:
        if not frappe.db.exists("Monument Type", t["monument_type_name"]):
            doc = frappe.new_doc("Monument Type")
            doc.update(t)
            doc.insert(ignore_permissions=True)
    frappe.db.commit()


def create_default_fee_types():
    types = [
        {
            "fee_type_name": "Plot Purchase",
            "description": "Purchase of a burial plot",
            "default_amount": 500.00,
        },
        {
            "fee_type_name": "Interment Fee",
            "description": "Fee for opening and closing a grave",
            "default_amount": 350.00,
        },
        {
            "fee_type_name": "Monument Setting Fee",
            "description": "Fee for installing a monument or headstone",
            "default_amount": 150.00,
        },
        {
            "fee_type_name": "Annual Maintenance",
            "description": "Annual cemetery maintenance fee",
            "default_amount": 50.00,
        },
        {
            "fee_type_name": "Cremation Interment",
            "description": "Fee for cremation burial",
            "default_amount": 200.00,
        },
        {
            "fee_type_name": "Deed Transfer",
            "description": "Fee for transferring plot ownership",
            "default_amount": 25.00,
        },
    ]
    for t in types:
        if not frappe.db.exists("Cemetery Fee Type", t["fee_type_name"]):
            doc = frappe.new_doc("Cemetery Fee Type")
            doc.update(t)
            doc.is_active = 1
            doc.flags.ignore_mandatory = True
            doc.insert(ignore_permissions=True)
    frappe.db.commit()


def create_cemetery_manager_role():
    if not frappe.db.exists("Role", "Cemetery Manager"):
        doc = frappe.new_doc("Role")
        doc.role_name = "Cemetery Manager"
        doc.desk_access = 1
        doc.insert(ignore_permissions=True)
    frappe.db.commit()


def create_workspace_sidebar():
    if frappe.db.exists("Workspace Sidebar", "Cemetery Management"):
        frappe.delete_doc(
            "Workspace Sidebar", "Cemetery Management",
            ignore_permissions=True, force=True
        )

    doc = frappe.new_doc("Workspace Sidebar")
    doc.name = "Cemetery Management"
    doc.title = "Cemetery Management"
    doc.header_icon = "map-pin"
    doc.module = "Cemetery Management"
    doc.standard = 0

    sidebar_items = [
        # Home
        {"label": "Home", "link_type": "Workspace", "type": "Link",
         "link_to": "Cemetery Management", "child": 0, "collapsible": 1,
         "indent": 0, "icon": "home"},

        # Cemetery Records
        {"label": "Cemetery Records", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "map-pin"},
        {"label": "Cemetery", "link_type": "DocType", "type": "Link",
         "link_to": "Cemetery", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Burial Record", "link_type": "DocType", "type": "Link",
         "link_to": "Burial Record", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Burial Plot", "link_type": "DocType", "type": "Link",
         "link_to": "Burial Plot", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Memorial Tribute", "link_type": "DocType", "type": "Link",
         "link_to": "Memorial Tribute", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # Operations
        {"label": "Operations", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "tool"},
        {"label": "Cemetery Work Order", "link_type": "DocType", "type": "Link",
         "link_to": "Cemetery Work Order", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Work Order Summary", "link_type": "Report", "type": "Link",
         "link_to": "Work Order Summary", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # Sales & Finance
        {"label": "Sales & Finance", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "income"},
        {"label": "Plot Sale", "link_type": "DocType", "type": "Link",
         "link_to": "Plot Sale", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Cemetery Service Invoice", "link_type": "DocType", "type": "Link",
         "link_to": "Cemetery Service Invoice", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Cemetery Fee Type", "link_type": "DocType", "type": "Link",
         "link_to": "Cemetery Fee Type", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Cemetery Price List", "link_type": "DocType", "type": "Link",
         "link_to": "Cemetery Price List", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Journal Entry", "link_type": "DocType", "type": "Link",
         "link_to": "Journal Entry", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Chart of Accounts", "link_type": "DocType", "type": "Link",
         "link_to": "Account", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # Pre-Need Sales
        {"label": "Pre-Need Sales", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "file"},
        {"label": "Pre-Need Contract", "link_type": "DocType", "type": "Link",
         "link_to": "Pre-Need Contract", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Contract Payment", "link_type": "DocType", "type": "Link",
         "link_to": "Contract Payment", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Pre-Need Contract Status", "link_type": "Report", "type": "Link",
         "link_to": "Pre-Need Contract Status", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Payment Schedule", "link_type": "Report", "type": "Link",
         "link_to": "Payment Schedule", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # Trust Funds
        {"label": "Trust Funds", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "bank"},
        {"label": "Perpetual Care Trust", "link_type": "DocType", "type": "Link",
         "link_to": "Perpetual Care Trust", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Trust Transaction", "link_type": "DocType", "type": "Link",
         "link_to": "Trust Transaction", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Trust Fund Balance", "link_type": "Report", "type": "Link",
         "link_to": "Trust Fund Balance", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Trust Transaction History", "link_type": "Report", "type": "Link",
         "link_to": "Trust Transaction History", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # People & CRM
        {"label": "People & CRM", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "users"},
        {"label": "Plot Owner", "link_type": "DocType", "type": "Link",
         "link_to": "Plot Owner", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Family Group", "link_type": "DocType", "type": "Link",
         "link_to": "Family Group", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Contact Log", "link_type": "DocType", "type": "Link",
         "link_to": "Contact Log", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Aftercare Schedule", "link_type": "DocType", "type": "Link",
         "link_to": "Aftercare Schedule", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Funeral Home", "link_type": "DocType", "type": "Link",
         "link_to": "Funeral Home", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Aftercare Due", "link_type": "Report", "type": "Link",
         "link_to": "Aftercare Due", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Contact Activity", "link_type": "Report", "type": "Link",
         "link_to": "Contact Activity", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # Cremation & Tracking
        {"label": "Cremation & Tracking", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "file"},
        {"label": "Remains Tracking", "link_type": "DocType", "type": "Link",
         "link_to": "Remains Tracking", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # Reports
        {"label": "Reports", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "chart"},
        {"label": "Cemetery Occupancy", "link_type": "Report", "type": "Link",
         "link_to": "Cemetery Occupancy", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Burial Records Report", "link_type": "Report", "type": "Link",
         "link_to": "Burial Records Report", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Cemetery Financial Summary", "link_type": "Report", "type": "Link",
         "link_to": "Cemetery Financial Summary", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Perpetual Care Fund", "link_type": "Report", "type": "Link",
         "link_to": "Perpetual Care Fund", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Veteran Burial Report", "link_type": "Report", "type": "Link",
         "link_to": "Veteran Burial Report", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Demographic Analysis", "link_type": "Report", "type": "Link",
         "link_to": "Demographic Analysis", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Revenue Forecast", "link_type": "Report", "type": "Link",
         "link_to": "Revenue Forecast", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},

        # Settings
        {"label": "Settings", "link_type": "DocType", "type": "Section Break",
         "link_to": None, "child": 0, "collapsible": 1, "indent": 1, "icon": "setting-gear"},
        {"label": "Monument Type", "link_type": "DocType", "type": "Link",
         "link_to": "Monument Type", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Contract Template", "link_type": "DocType", "type": "Link",
         "link_to": "Contract Template", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
        {"label": "Cemetery Settings", "link_type": "DocType", "type": "Link",
         "link_to": "Cemetery Settings", "child": 1, "collapsible": 1, "indent": 0, "icon": ""},
    ]

    for idx, item in enumerate(sidebar_items, 1):
        item["idx"] = idx
        doc.append("items", item)

    doc.insert(ignore_permissions=True)
    frappe.db.commit()


def create_desktop_icon():
    if not frappe.db.exists("Desktop Icon", "Cemetery Management"):
        doc = frappe.new_doc("Desktop Icon")
        doc.label = "Cemetery Management"
        doc.icon_type = "Link"
        doc.link_type = "Workspace Sidebar"
        doc.link_to = "Cemetery Management"
        doc.icon = "map-pin"
        doc.app = "cemetery_management"
        doc.bg_color = "gray"
        doc.hidden = 0
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
