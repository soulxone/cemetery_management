import frappe
from frappe.utils import getdate


def execute(filters=None):
    columns = [
        {"fieldname": "name", "label": "ID", "fieldtype": "Link", "options": "Burial Record", "width": 150},
        {"fieldname": "full_name", "label": "Name", "fieldtype": "Data", "width": 200},
        {"fieldname": "maiden_name", "label": "Maiden Name", "fieldtype": "Data", "width": 120},
        {"fieldname": "date_of_birth", "label": "Born", "fieldtype": "Date", "width": 110},
        {"fieldname": "date_of_death", "label": "Died", "fieldtype": "Date", "width": 110},
        {"fieldname": "age_at_death", "label": "Age", "fieldtype": "Data", "width": 80},
        {"fieldname": "cemetery", "label": "Cemetery", "fieldtype": "Link", "options": "Cemetery", "width": 180},
        {"fieldname": "burial_plot", "label": "Plot", "fieldtype": "Link", "options": "Burial Plot", "width": 150},
        {"fieldname": "interment_date", "label": "Interment Date", "fieldtype": "Date", "width": 120},
        {"fieldname": "is_veteran", "label": "Veteran", "fieldtype": "Check", "width": 70},
        {"fieldname": "military_branch", "label": "Branch", "fieldtype": "Data", "width": 100},
    ]

    conditions = ["docstatus = 1"]

    if filters:
        if filters.get("cemetery"):
            conditions.append(f"cemetery = {frappe.db.escape(filters['cemetery'])}")
        if filters.get("from_date"):
            conditions.append(f"date_of_death >= '{getdate(filters['from_date'])}'")
        if filters.get("to_date"):
            conditions.append(f"date_of_death <= '{getdate(filters['to_date'])}'")
        if filters.get("is_veteran"):
            conditions.append("is_veteran = 1")
        if filters.get("section"):
            conditions.append(f"burial_plot IN (SELECT name FROM `tabBurial Plot` WHERE section = {frappe.db.escape(filters['section'])})")

    where = " AND ".join(conditions)

    data = frappe.db.sql(f"""
        SELECT
            name, full_name, maiden_name, date_of_birth, date_of_death,
            age_at_death, cemetery, burial_plot, interment_date,
            is_veteran, military_branch
        FROM `tabBurial Record`
        WHERE {where}
        ORDER BY last_name, first_name
    """, as_dict=True)

    return columns, data
