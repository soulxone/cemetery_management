import frappe
from frappe.utils import getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "name", "label": "Contract", "fieldtype": "Link", "options": "Pre-Need Contract", "width": 150},
		{"fieldname": "buyer_name", "label": "Buyer", "fieldtype": "Data", "width": 180},
		{"fieldname": "burial_plot", "label": "Plot", "fieldtype": "Link", "options": "Burial Plot", "width": 150},
		{"fieldname": "contract_date", "label": "Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "total_amount", "label": "Total", "fieldtype": "Currency", "width": 110},
		{"fieldname": "total_paid", "label": "Paid", "fieldtype": "Currency", "width": 110},
		{"fieldname": "balance_remaining", "label": "Balance", "fieldtype": "Currency", "width": 110},
		{"fieldname": "payments_completed", "label": "Payments", "fieldtype": "Int", "width": 80},
		{"fieldname": "contract_status", "label": "Status", "fieldtype": "Data", "width": 100},
		{"fieldname": "next_payment_due", "label": "Next Due", "fieldtype": "Date", "width": 110},
	]


def get_data(filters):
	conditions = "docstatus = 1"

	if filters:
		if filters.get("contract_status"):
			conditions += f" AND contract_status = {frappe.db.escape(filters['contract_status'])}"
		if filters.get("from_date"):
			conditions += f" AND contract_date >= '{getdate(filters['from_date'])}'"
		if filters.get("to_date"):
			conditions += f" AND contract_date <= '{getdate(filters['to_date'])}'"
		if filters.get("cemetery"):
			conditions += f" AND cemetery = {frappe.db.escape(filters['cemetery'])}"

	return frappe.db.sql(
		f"""
		SELECT
			name, buyer_name, burial_plot, contract_date,
			total_amount, total_paid, balance_remaining,
			payments_completed, contract_status, next_payment_due
		FROM `tabPre-Need Contract`
		WHERE {conditions}
		ORDER BY contract_date DESC
		""",
		as_dict=True,
	)
