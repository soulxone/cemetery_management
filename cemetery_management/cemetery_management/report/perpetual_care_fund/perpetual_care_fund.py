import frappe
from frappe.utils import flt, getdate


def execute(filters=None):
    columns = [
        {"fieldname": "sale_date", "label": "Date", "fieldtype": "Date", "width": 110},
        {"fieldname": "name", "label": "Plot Sale", "fieldtype": "Link", "options": "Plot Sale", "width": 150},
        {"fieldname": "burial_plot", "label": "Plot", "fieldtype": "Link", "options": "Burial Plot", "width": 150},
        {"fieldname": "buyer_name", "label": "Buyer", "fieldtype": "Data", "width": 180},
        {"fieldname": "amount", "label": "Sale Amount", "fieldtype": "Currency", "width": 120},
        {"fieldname": "perpetual_care_amount", "label": "Care Contribution", "fieldtype": "Currency", "width": 140},
        {"fieldname": "cumulative", "label": "Cumulative Fund", "fieldtype": "Currency", "width": 140},
    ]

    conditions = "docstatus = 1 AND perpetual_care_amount > 0"
    if filters:
        if filters.get("from_date"):
            conditions += f" AND sale_date >= '{getdate(filters['from_date'])}'"
        if filters.get("to_date"):
            conditions += f" AND sale_date <= '{getdate(filters['to_date'])}'"
        if filters.get("cemetery"):
            conditions += f" AND cemetery = {frappe.db.escape(filters['cemetery'])}"

    data = frappe.db.sql(f"""
        SELECT
            sale_date, name, burial_plot, buyer_name,
            amount, perpetual_care_amount
        FROM `tabPlot Sale`
        WHERE {conditions}
        ORDER BY sale_date ASC
    """, as_dict=True)

    # Calculate cumulative totals
    cumulative = 0
    for row in data:
        cumulative += flt(row.perpetual_care_amount)
        row["cumulative"] = cumulative

    return columns, data
