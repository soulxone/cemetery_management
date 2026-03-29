import frappe
from frappe.model.document import Document
from frappe.utils import today


class MemorialTribute(Document):
	def before_save(self):
		if self.is_approved and not self.approved_by:
			self.approved_by = frappe.session.user
			self.approved_date = today()
		elif not self.is_approved:
			self.approved_by = None
			self.approved_date = None
