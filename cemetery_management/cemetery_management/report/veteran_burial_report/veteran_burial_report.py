import frappe
from frappe.utils import getdate


def execute(filters=None):
	columns = [
		{"fieldname": "name", "label": "Record", "fieldtype": "Link", "options": "Burial Record", "width": 150},
		{"fieldname": "full_name", "label": "Name", "fieldtype": "Data", "width": 200},
		{"fieldname": "date_of_birth", "label": "Born", "fieldtype": "Date", "width": 100},
		{"fieldname": "date_of_death", "label": "Died", "fieldtype": "Date", "width": 100},
		{"fieldname": "military_branch", "label": "Branch", "fieldtype": "Data", "width": 120},
		{"fieldname": "military_rank", "label": "Rank", "fieldtype": "Data", "width": 100},
		{"fieldname": "military_war", "label": "War/Conflict", "fieldtype": "Data", "width": 130},
		{"fieldname": "burial_plot", "label": "Plot", "fieldtype": "Link", "options": "Burial Plot", "width": 150},
		{"fieldname": "cemetery", "label": "Cemetery", "fieldtype": "Link", "options": "Cemetery", "width": 180},
	]

	conditions = "docstatus = 1 AND is_veteran = 1"
	if filters:
		if filters.get("military_branch"):
			conditions += f" AND military_branch = {frappe.db.escape(filters['military_branch'])}"
		if filters.get("military_war"):
			conditions += f" AND military_war = {frappe.db.escape(filters['military_war'])}"
		if filters.get("cemetery"):
			conditions += f" AND cemetery = {frappe.db.escape(filters['cemetery'])}"

	data = frappe.db.sql(
		f"""
		SELECT name, full_name, date_of_birth, date_of_death,
			military_branch, military_rank, military_war,
			burial_plot, cemetery
		FROM `tabBurial Record`
		WHERE {conditions}
		ORDER BY military_branch, last_name, first_name
		""",
		as_dict=True,
	)

	return columns, data
