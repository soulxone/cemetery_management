import frappe
from frappe import _
from frappe.model.document import Document


VALID_TRANSITIONS = {
	"Received": ["In Storage", "Released", "Interred"],
	"In Storage": ["Released", "Interred"],
	"Released": ["Interred"],
	"Interred": [],
}


class RemainsTracking(Document):
	def validate(self):
		self.validate_status_transition()

	def validate_status_transition(self):
		if self.is_new():
			return
		old_status = frappe.db.get_value("Remains Tracking", self.name, "status")
		if old_status and old_status != self.status:
			valid = VALID_TRANSITIONS.get(old_status, [])
			if self.status not in valid:
				frappe.throw(
					_("Cannot change status from {0} to {1}. Valid transitions: {2}").format(
						old_status, self.status, ", ".join(valid) or "None"
					)
				)
