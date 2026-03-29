import frappe
from frappe.utils import getdate, today


def execute(filters=None):
	columns = [
		{"fieldname": "name", "label": "ID", "fieldtype": "Link", "options": "Aftercare Schedule", "width": 150},
		{"fieldname": "deceased_name", "label": "Deceased", "fieldtype": "Data", "width": 180},
		{"fieldname": "schedule_type", "label": "Type", "fieldtype": "Data", "width": 100},
		{"fieldname": "scheduled_date", "label": "Due Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "days_until", "label": "Days Until", "fieldtype": "Int", "width": 90},
		{"fieldname": "plot_owner", "label": "Plot Owner", "fieldtype": "Link", "options": "Plot Owner", "width": 150},
		{"fieldname": "family_group", "label": "Family", "fieldtype": "Link", "options": "Family Group", "width": 150},
		{"fieldname": "completed", "label": "Done", "fieldtype": "Check", "width": 60},
	]

	conditions = "completed = 0"
	if filters:
		if filters.get("schedule_type"):
			conditions += f" AND schedule_type = {frappe.db.escape(filters['schedule_type'])}"
		if filters.get("from_date"):
			conditions += f" AND scheduled_date >= '{getdate(filters['from_date'])}'"
		if filters.get("to_date"):
			conditions += f" AND scheduled_date <= '{getdate(filters['to_date'])}'"

	data = frappe.db.sql(
		f"""
		SELECT name, deceased_name, schedule_type, scheduled_date,
			plot_owner, family_group, completed
		FROM `tabAftercare Schedule`
		WHERE {conditions}
		ORDER BY scheduled_date ASC
		""",
		as_dict=True,
	)

	today_date = getdate(today())
	for row in data:
		if row.scheduled_date:
			delta = (getdate(row.scheduled_date) - today_date).days
			row["days_until"] = delta

	return columns, data
