import frappe
from frappe.utils import getdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "name", "label": "ID", "fieldtype": "Link", "options": "Cemetery Work Order", "width": 150},
		{"fieldname": "title", "label": "Title", "fieldtype": "Data", "width": 250},
		{"fieldname": "work_order_type", "label": "Type", "fieldtype": "Data", "width": 130},
		{"fieldname": "priority", "label": "Priority", "fieldtype": "Data", "width": 90},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
		{"fieldname": "assigned_to", "label": "Assigned To", "fieldtype": "Link", "options": "User", "width": 150},
		{"fieldname": "scheduled_date", "label": "Scheduled Date", "fieldtype": "Date", "width": 120},
		{"fieldname": "completion_date", "label": "Completion Date", "fieldtype": "Date", "width": 120},
		{"fieldname": "cemetery", "label": "Cemetery", "fieldtype": "Link", "options": "Cemetery", "width": 180},
		{"fieldname": "burial_plot", "label": "Plot", "fieldtype": "Link", "options": "Burial Plot", "width": 150},
	]


def get_data(filters):
	conditions = "docstatus < 2"

	if filters:
		if filters.get("status"):
			conditions += f" AND status = {frappe.db.escape(filters['status'])}"
		if filters.get("work_order_type"):
			conditions += f" AND work_order_type = {frappe.db.escape(filters['work_order_type'])}"
		if filters.get("assigned_to"):
			conditions += f" AND assigned_to = {frappe.db.escape(filters['assigned_to'])}"
		if filters.get("cemetery"):
			conditions += f" AND cemetery = {frappe.db.escape(filters['cemetery'])}"
		if filters.get("from_date"):
			conditions += f" AND scheduled_date >= '{getdate(filters['from_date'])}'"
		if filters.get("to_date"):
			conditions += f" AND scheduled_date <= '{getdate(filters['to_date'])}'"

	return frappe.db.sql(
		f"""
		SELECT
			name, title, work_order_type, priority, status,
			assigned_to, scheduled_date, completion_date,
			cemetery, burial_plot
		FROM `tabCemetery Work Order`
		WHERE {conditions}
		ORDER BY scheduled_date DESC, priority DESC
		""",
		as_dict=True,
	)
