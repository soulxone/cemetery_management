import frappe
from frappe.utils import flt, getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "name", "label": "Payment", "fieldtype": "Link", "options": "Contract Payment", "width": 150},
		{"fieldname": "pre_need_contract", "label": "Contract", "fieldtype": "Link", "options": "Pre-Need Contract", "width": 150},
		{"fieldname": "buyer_name", "label": "Buyer", "fieldtype": "Data", "width": 180},
		{"fieldname": "payment_date", "label": "Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "amount", "label": "Amount", "fieldtype": "Currency", "width": 110},
		{"fieldname": "payment_method", "label": "Method", "fieldtype": "Data", "width": 100},
		{"fieldname": "payment_reference", "label": "Reference", "fieldtype": "Data", "width": 130},
		{"fieldname": "cumulative", "label": "Cumulative", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	conditions = "cp.docstatus = 1"

	if filters:
		if filters.get("pre_need_contract"):
			conditions += f" AND cp.pre_need_contract = {frappe.db.escape(filters['pre_need_contract'])}"
		if filters.get("from_date"):
			conditions += f" AND cp.payment_date >= '{getdate(filters['from_date'])}'"
		if filters.get("to_date"):
			conditions += f" AND cp.payment_date <= '{getdate(filters['to_date'])}'"

	data = frappe.db.sql(
		f"""
		SELECT
			cp.name, cp.pre_need_contract, cp.buyer_name,
			cp.payment_date, cp.amount, cp.payment_method,
			cp.payment_reference
		FROM `tabContract Payment` cp
		WHERE {conditions}
		ORDER BY cp.pre_need_contract, cp.payment_date ASC
		""",
		as_dict=True,
	)

	# Compute cumulative per contract
	cumulative = {}
	for row in data:
		contract = row.pre_need_contract
		cumulative[contract] = flt(cumulative.get(contract, 0)) + flt(row.amount)
		row["cumulative"] = cumulative[contract]

	return data
