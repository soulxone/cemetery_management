import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ContractPayment(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Payment amount must be greater than zero"))

	def on_submit(self):
		self.create_journal_entry()
		self.update_contract()

	def on_cancel(self):
		self.cancel_journal_entry()
		self.revert_contract()

	def create_journal_entry(self):
		if self.journal_entry:
			return

		settings = frappe.get_single("Cemetery Settings")
		deferred_account = settings.pre_need_deferred_revenue_account
		if not deferred_account:
			frappe.throw(
				_("Please set Pre-Need Deferred Revenue Account in Cemetery Settings")
			)

		# Get first fee type from the contract services for the income account
		contract = frappe.get_doc("Pre-Need Contract", self.pre_need_contract)
		if not contract.services:
			frappe.throw(_("Contract has no services defined"))

		fee_type = frappe.get_doc("Cemetery Fee Type", contract.services[0].cemetery_fee_type)

		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.payment_date
		je.company = self.company
		je.voucher_type = "Journal Entry"

		je.append("accounts", {
			"account": fee_type.debit_account,
			"debit_in_account_currency": flt(self.amount),
		})
		je.append("accounts", {
			"account": deferred_account,
			"credit_in_account_currency": flt(self.amount),
		})

		je.remark = (
			f"Pre-Need Contract Payment {self.name} - "
			f"Contract {self.pre_need_contract} - {self.buyer_name}"
		)
		je.insert(ignore_permissions=True)
		je.submit()

		self.db_set("journal_entry", je.name)

	def cancel_journal_entry(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.cancel()
			self.db_set("journal_entry", None)

	def update_contract(self):
		if self.pre_need_contract:
			contract = frappe.get_doc("Pre-Need Contract", self.pre_need_contract)
			contract.update_payment_tracking(flt(self.amount))

	def revert_contract(self):
		if self.pre_need_contract:
			contract = frappe.get_doc("Pre-Need Contract", self.pre_need_contract)
			contract.revert_payment_tracking(flt(self.amount))
