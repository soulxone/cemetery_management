import frappe
from frappe.utils import getdate


def execute(filters=None):
	columns = [
		{"fieldname": "name", "label": "Transaction", "fieldtype": "Link", "options": "Trust Transaction", "width": 150},
		{"fieldname": "transaction_date", "label": "Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "perpetual_care_trust", "label": "Trust", "fieldtype": "Link", "options": "Perpetual Care Trust", "width": 150},
		{"fieldname": "transaction_type", "label": "Type", "fieldtype": "Data", "width": 110},
		{"fieldname": "amount", "label": "Amount", "fieldtype": "Currency", "width": 120},
		{"fieldname": "reference_doctype", "label": "Ref Type", "fieldtype": "Data", "width": 120},
		{"fieldname": "reference_name", "label": "Reference", "fieldtype": "Data", "width": 150},
		{"fieldname": "description", "label": "Description", "fieldtype": "Data", "width": 200},
	]

	conditions = "docstatus = 1"
	if filters:
		if filters.get("perpetual_care_trust"):
			conditions += f" AND perpetual_care_trust = {frappe.db.escape(filters['perpetual_care_trust'])}"
		if filters.get("transaction_type"):
			conditions += f" AND transaction_type = {frappe.db.escape(filters['transaction_type'])}"
		if filters.get("from_date"):
			conditions += f" AND transaction_date >= '{getdate(filters['from_date'])}'"
		if filters.get("to_date"):
			conditions += f" AND transaction_date <= '{getdate(filters['to_date'])}'"

	data = frappe.db.sql(
		f"""
		SELECT name, transaction_date, perpetual_care_trust,
			transaction_type, amount, reference_doctype,
			reference_name, description
		FROM `tabTrust Transaction`
		WHERE {conditions}
		ORDER BY transaction_date DESC
		""",
		as_dict=True,
	)

	return columns, data
