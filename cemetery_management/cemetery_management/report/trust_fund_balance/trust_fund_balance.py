import frappe
from frappe.utils import flt


def execute(filters=None):
	columns = [
		{"fieldname": "name", "label": "Trust", "fieldtype": "Link", "options": "Perpetual Care Trust", "width": 150},
		{"fieldname": "trust_name", "label": "Trust Name", "fieldtype": "Data", "width": 200},
		{"fieldname": "fund_type", "label": "Type", "fieldtype": "Data", "width": 120},
		{"fieldname": "opening_balance", "label": "Opening Balance", "fieldtype": "Currency", "width": 130},
		{"fieldname": "contributions", "label": "Contributions", "fieldtype": "Currency", "width": 130},
		{"fieldname": "earnings", "label": "Earnings", "fieldtype": "Currency", "width": 120},
		{"fieldname": "withdrawals", "label": "Withdrawals", "fieldtype": "Currency", "width": 120},
		{"fieldname": "fees", "label": "Fees", "fieldtype": "Currency", "width": 100},
		{"fieldname": "current_balance", "label": "Current Balance", "fieldtype": "Currency", "width": 140},
	]

	trusts = frappe.get_all(
		"Perpetual Care Trust",
		filters={"docstatus": 1},
		fields=["name", "trust_name", "fund_type", "opening_balance", "current_balance"],
	)

	data = []
	for trust in trusts:
		txn_summary = frappe.db.sql(
			"""
			SELECT transaction_type, SUM(amount) as total
			FROM `tabTrust Transaction`
			WHERE perpetual_care_trust = %s AND docstatus = 1
			GROUP BY transaction_type
			""",
			trust.name,
			as_dict=True,
		)

		txn_map = {t.transaction_type: flt(t.total) for t in txn_summary}

		data.append({
			"name": trust.name,
			"trust_name": trust.trust_name,
			"fund_type": trust.fund_type,
			"opening_balance": trust.opening_balance,
			"contributions": txn_map.get("Contribution", 0),
			"earnings": txn_map.get("Earnings", 0),
			"withdrawals": txn_map.get("Withdrawal", 0),
			"fees": txn_map.get("Fee", 0),
			"current_balance": trust.current_balance,
		})

	return columns, data
