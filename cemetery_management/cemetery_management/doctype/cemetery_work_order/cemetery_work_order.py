import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today


class CemeteryWorkOrder(Document):
	def validate(self):
		self.set_title()
		self.validate_dates()
		self.check_interment_conflicts()

	def set_title(self):
		parts = [self.work_order_type or "Work Order"]
		if self.burial_plot:
			parts.append(f"- {self.burial_plot}")
		if self.work_order_type == "Interment" and self.burial_record:
			full_name = frappe.db.get_value("Burial Record", self.burial_record, "full_name")
			if full_name:
				parts.append(f"({full_name})")
		self.title = " ".join(parts)

	def validate_dates(self):
		if self.completion_date and self.scheduled_date:
			if getdate(self.completion_date) < getdate(self.scheduled_date):
				frappe.throw(_("Completion Date cannot be before Scheduled Date"))

	def check_interment_conflicts(self):
		if self.work_order_type != "Interment" or not self.burial_plot or not self.scheduled_date:
			return

		conflicts = frappe.db.sql(
			"""
			SELECT name FROM `tabCemetery Work Order`
			WHERE burial_plot = %s
				AND scheduled_date = %s
				AND work_order_type = 'Interment'
				AND docstatus < 2
				AND name != %s
			""",
			(self.burial_plot, self.scheduled_date, self.name or ""),
			as_dict=True,
		)
		if conflicts:
			frappe.throw(
				_("An interment is already scheduled for plot {0} on {1} ({2})").format(
					self.burial_plot, self.scheduled_date, conflicts[0].name
				)
			)

	def on_submit(self):
		if not self.completion_date:
			self.db_set("completion_date", today())
		if self.status == "Open":
			self.db_set("status", "Completed")

	def on_cancel(self):
		self.db_set("status", "Cancelled")

	@staticmethod
	def get_events(start, end, filters=None):
		"""Return events for Frappe calendar view."""
		conditions = ""
		if filters:
			if filters.get("cemetery"):
				conditions += f" AND cemetery = {frappe.db.escape(filters['cemetery'])}"
			if filters.get("work_order_type"):
				conditions += f" AND work_order_type = {frappe.db.escape(filters['work_order_type'])}"

		events = frappe.db.sql(
			f"""
			SELECT
				name, title, scheduled_date, completion_date,
				work_order_type, priority, status
			FROM `tabCemetery Work Order`
			WHERE docstatus < 2
				AND scheduled_date BETWEEN %s AND %s
				{conditions}
			""",
			(start, end),
			as_dict=True,
		)

		color_map = {
			"Interment": "#e74c3c",
			"Maintenance": "#3498db",
			"Monument Setting": "#2ecc71",
			"Grave Preparation": "#f39c12",
			"Landscaping": "#1abc9c",
			"Repair": "#9b59b6",
			"Exhumation": "#e67e22",
			"Cleanup": "#95a5a6",
		}

		for e in events:
			e["color"] = color_map.get(e.get("work_order_type"), "#7f8c8d")
			if not e.get("completion_date"):
				e["completion_date"] = e["scheduled_date"]

		return events
