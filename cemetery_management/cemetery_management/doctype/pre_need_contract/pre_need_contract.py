import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, add_months, today


class PreNeedContract(Document):
	def validate(self):
		self.calculate_totals()
		self.compute_installment()
		self.compute_balance()

	def calculate_totals(self):
		total = 0
		for item in self.services:
			item.amount = flt(item.quantity) * flt(item.rate)
			total += flt(item.amount)
		self.total_amount = total

	def compute_installment(self):
		if cint(self.number_of_payments) > 0:
			self.installment_amount = flt(self.total_amount) / cint(self.number_of_payments)
		else:
			self.installment_amount = flt(self.total_amount)

	def compute_balance(self):
		self.balance_remaining = flt(self.total_amount) - flt(self.total_paid)

	def on_submit(self):
		self.db_set("contract_status", "Active")
		if self.burial_plot:
			frappe.db.set_value("Burial Plot", self.burial_plot, "status", "Pre-Need")

	def on_cancel(self):
		self.db_set("contract_status", "Cancelled")
		if self.burial_plot:
			plot = frappe.get_doc("Burial Plot", self.burial_plot)
			if plot.status == "Pre-Need" and cint(plot.current_interments) == 0:
				frappe.db.set_value("Burial Plot", self.burial_plot, "status", "Available")

	def update_payment_tracking(self, payment_amount):
		"""Called by Contract Payment on_submit."""
		self.reload()
		self.db_set("payments_completed", cint(self.payments_completed) + 1)
		self.db_set("total_paid", flt(self.total_paid) + flt(payment_amount))
		self.db_set("balance_remaining", flt(self.total_amount) - flt(self.total_paid) - flt(payment_amount))

		# Compute next payment due
		frequency_months = {
			"Monthly": 1,
			"Quarterly": 3,
			"Semi-Annual": 6,
			"Annual": 12,
			"Lump Sum": 0,
		}
		months = frequency_months.get(self.payment_frequency, 1)
		if months and flt(self.balance_remaining) > flt(payment_amount):
			self.db_set("next_payment_due", add_months(today(), months))
		else:
			self.db_set("next_payment_due", None)

		# Check if fulfilled
		remaining = flt(self.total_amount) - flt(self.total_paid) - flt(payment_amount)
		if remaining <= 0:
			self.db_set("contract_status", "Fulfilled")
			self.db_set("fulfillment_date", today())

	def revert_payment_tracking(self, payment_amount):
		"""Called by Contract Payment on_cancel."""
		self.reload()
		self.db_set("payments_completed", max(0, cint(self.payments_completed) - 1))
		self.db_set("total_paid", max(0, flt(self.total_paid) - flt(payment_amount)))
		self.db_set("balance_remaining", flt(self.total_amount) - max(0, flt(self.total_paid) - flt(payment_amount)))

		if self.contract_status == "Fulfilled":
			self.db_set("contract_status", "Active")
			self.db_set("fulfillment_date", None)
