import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, date_diff, getdate


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
