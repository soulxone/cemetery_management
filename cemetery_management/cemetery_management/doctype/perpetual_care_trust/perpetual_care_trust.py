import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PerpetualCareTrust(Document):
	def on_submit(self):
		self.db_set("current_balance", flt(self.opening_balance))

	def on_cancel(self):
		# Check no trust transactions exist
		txns = frappe.db.count("Trust Transaction", {
			"perpetual_care_trust": self.name,
			"docstatus": 1,
		})
		if txns:
			frappe.throw(
				_("Cannot cancel trust with {0} active transaction(s). Cancel them first.").format(txns)
			)

	def update_balance(self, amount, transaction_type):
		"""Update current_balance based on transaction type."""
		self.reload()
		current = flt(self.current_balance)
		if transaction_type in ("Contribution", "Earnings"):
			new_balance = current + flt(amount)
		elif transaction_type in ("Withdrawal", "Fee"):
			new_balance = current - flt(amount)
		else:
			new_balance = current
		self.db_set("current_balance", new_balance)
