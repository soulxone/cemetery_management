import frappe
from frappe.utils import flt, getdate


def execute(filters=None):
    columns = [
        {"fieldname": "category", "label": "Category", "fieldtype": "Data", "width": 250},
        {"fieldname": "count", "label": "Count", "fieldtype": "Int", "width": 80},
        {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency", "width": 150},
    ]

    conditions = "docstatus = 1"
    if filters:
        if filters.get("from_date"):
            conditions += f" AND sale_date >= '{getdate(filters['from_date'])}'"
        if filters.get("to_date"):
            conditions += f" AND sale_date <= '{getdate(filters['to_date'])}'"
        if filters.get("cemetery"):
            conditions += f" AND cemetery = {frappe.db.escape(filters['cemetery'])}"

    data = []

    # Plot Sales
    plot_sales = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt, SUM(amount) as total
        FROM `tabPlot Sale`
        WHERE {conditions}
    """, as_dict=True)

    if plot_sales:
        data.append({
            "category": "Plot Sales Revenue",
            "count": plot_sales[0].cnt or 0,
            "amount": flt(plot_sales[0].total),
        })

    # Perpetual Care
    perp_care = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt, SUM(perpetual_care_amount) as total
        FROM `tabPlot Sale`
        WHERE {conditions} AND perpetual_care_amount > 0
    """, as_dict=True)

    if perp_care:
        data.append({
            "category": "Perpetual Care Fund Contributions",
            "count": perp_care[0].cnt or 0,
            "amount": flt(perp_care[0].total),
        })

    # Service Invoices
    svc_conditions = "docstatus = 1"
    if filters:
        if filters.get("from_date"):
            svc_conditions += f" AND invoice_date >= '{getdate(filters['from_date'])}'"
        if filters.get("to_date"):
            svc_conditions += f" AND invoice_date <= '{getdate(filters['to_date'])}'"

    svc_invoices = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt, SUM(total_amount) as total
        FROM `tabCemetery Service Invoice`
        WHERE {svc_conditions}
    """, as_dict=True)

    if svc_invoices:
        data.append({
            "category": "Service Invoice Revenue",
            "count": svc_invoices[0].cnt or 0,
            "amount": flt(svc_invoices[0].total),
        })

    # Outstanding invoices
    outstanding = frappe.db.sql(f"""
        SELECT COUNT(*) as cnt, SUM(total_amount) as total
        FROM `tabCemetery Service Invoice`
        WHERE {svc_conditions} AND payment_status != 'Paid'
    """, as_dict=True)

    if outstanding:
        data.append({
            "category": "Outstanding Invoices",
            "count": outstanding[0].cnt or 0,
            "amount": flt(outstanding[0].total),
        })

    # Net revenue
    total_revenue = sum(flt(d.get("amount")) for d in data if d["category"] != "Outstanding Invoices" and d["category"] != "Perpetual Care Fund Contributions")
    data.append({
        "category": "Net Revenue (excl. Perpetual Care)",
        "count": "",
        "amount": total_revenue - flt(perp_care[0].total if perp_care else 0),
    })

    return columns, data
