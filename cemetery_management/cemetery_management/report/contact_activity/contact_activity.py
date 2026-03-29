import frappe
from frappe.utils import getdate


def execute(filters=None):
	columns = [
		{"fieldname": "name", "label": "ID", "fieldtype": "Link", "options": "Contact Log", "width": 150},
		{"fieldname": "contact_date", "label": "Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "contact_type", "label": "Type", "fieldtype": "Data", "width": 80},
		{"fieldname": "subject", "label": "Subject", "fieldtype": "Data", "width": 250},
		{"fieldname": "plot_owner", "label": "Plot Owner", "fieldtype": "Link", "options": "Plot Owner", "width": 150},
		{"fieldname": "family_group", "label": "Family", "fieldtype": "Link", "options": "Family Group", "width": 150},
		{"fieldname": "assigned_to", "label": "Assigned To", "fieldtype": "Link", "options": "User", "width": 150},
		{"fieldname": "follow_up_date", "label": "Follow-Up", "fieldtype": "Date", "width": 110},
		{"fieldname": "completed", "label": "Done", "fieldtype": "Check", "width": 60},
	]

	conditions = "1=1"
	if filters:
		if filters.get("contact_type"):
			conditions += f" AND contact_type = {frappe.db.escape(filters['contact_type'])}"
		if filters.get("plot_owner"):
			conditions += f" AND plot_owner = {frappe.db.escape(filters['plot_owner'])}"
		if filters.get("from_date"):
			conditions += f" AND contact_date >= '{getdate(filters['from_date'])}'"
		if filters.get("to_date"):
			conditions += f" AND contact_date <= '{getdate(filters['to_date'])}'"
		if filters.get("completed") == "No":
			conditions += " AND completed = 0"

	data = frappe.db.sql(
		f"""
		SELECT name, contact_date, contact_type, subject,
			plot_owner, family_group, assigned_to,
			follow_up_date, completed
		FROM `tabContact Log`
		WHERE {conditions}
		ORDER BY contact_date DESC
		""",
		as_dict=True,
	)

	return columns, data
