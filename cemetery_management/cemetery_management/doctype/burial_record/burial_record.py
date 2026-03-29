import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, cint, date_diff, getdate, today


class BurialRecord(Document):
	def validate(self):
		self.set_full_name()
		self.compute_age()
		self.validate_dates()

	def set_full_name(self):
		parts = [self.first_name, self.middle_name, self.last_name]
		self.full_name = " ".join(p for p in parts if p)

	def compute_age(self):
		if self.date_of_birth and self.date_of_death:
			birth = getdate(self.date_of_birth)
			death = getdate(self.date_of_death)
			years = death.year - birth.year
			if (death.month, death.day) < (birth.month, birth.day):
				years -= 1
			self.age_at_death = f"{years} years"
		else:
			self.age_at_death = ""

	def validate_dates(self):
		if self.date_of_birth and self.date_of_death:
			if getdate(self.date_of_death) < getdate(self.date_of_birth):
				frappe.throw(_("Date of death cannot be before date of birth"))

	def on_submit(self):
		self.update_plot_status()
		self.link_church_member()
		self.create_aftercare_schedules()

	def on_cancel(self):
		self.revert_plot_status()
		self.unlink_church_member()

	def update_plot_status(self):
		if self.burial_plot:
			plot = frappe.get_doc("Burial Plot", self.burial_plot)
			plot.current_interments = cint(plot.current_interments) + 1
			if plot.current_interments >= cint(plot.max_interments or 1):
				plot.status = "Occupied"
			plot.save(ignore_permissions=True)

	def revert_plot_status(self):
		if self.burial_plot:
			plot = frappe.get_doc("Burial Plot", self.burial_plot)
			plot.current_interments = max(0, cint(plot.current_interments) - 1)
			if plot.current_interments < cint(plot.max_interments or 1):
				plot.status = "Available"
			plot.save(ignore_permissions=True)

	def link_church_member(self):
		if self.church_member:
			frappe.db.set_value(
				"Church Member", self.church_member, "burial_record", self.name
			)

	def unlink_church_member(self):
		if self.church_member:
			frappe.db.set_value(
				"Church Member", self.church_member, "burial_record", None
			)

	def create_aftercare_schedules(self):
		"""Auto-create 30-day, 6-month, and anniversary aftercare schedules."""
		base_date = self.interment_date or today()

		# Get plot owner from burial plot if available
		plot_owner = None
		if self.burial_plot:
			plot_owner = frappe.db.get_value("Burial Plot", self.burial_plot, "plot_owner")

		schedules = [
			("30-Day", add_days(base_date, 30)),
			("6-Month", add_months(base_date, 6)),
			("Anniversary", add_months(base_date, 12)),
		]

		for schedule_type, scheduled_date in schedules:
			doc = frappe.new_doc("Aftercare Schedule")
			doc.burial_record = self.name
			doc.schedule_type = schedule_type
			doc.scheduled_date = scheduled_date
			if plot_owner:
				doc.plot_owner = plot_owner
			doc.insert(ignore_permissions=True)

		frappe.db.commit()
