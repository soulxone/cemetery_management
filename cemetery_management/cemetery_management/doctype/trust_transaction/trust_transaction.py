import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class TrustTransaction(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw(_("Amount must be greater than zero"))

	def on_submit(self):
		self.create_journal_entry()
		self.update_trust_balance()

	def on_cancel(self):
		self.cancel_journal_entry()
		self.revert_trust_balance()

	def create_journal_entry(self):
		if self.journal_entry:
			return

		trust = frappe.get_doc("Perpetual Care Trust", self.perpetual_care_trust)

		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.transaction_date
		je.company = self.company
		je.voucher_type = "Journal Entry"

		if self.transaction_type in ("Contribution", "Earnings"):
			# Debit cash/income, credit trust account
			settings = frappe.get_single("Cemetery Settings")
			debit_account = settings.perpetual_care_account or trust.trust_account
			je.append("accounts", {
				"account": debit_account,
				"debit_in_account_currency": flt(self.amount),
			})
			je.append("accounts", {
				"account": trust.trust_account,
				"credit_in_account_currency": flt(self.amount),
			})
		elif self.transaction_type in ("Withdrawal", "Fee"):
			# Debit trust account, credit expense/cash
			settings = frappe.get_single("Cemetery Settings")
			credit_account = settings.perpetual_care_account or trust.trust_account
			je.append("accounts", {
				"account": trust.trust_account,
				"debit_in_account_currency": flt(self.amount),
			})
			je.append("accounts", {
				"account": credit_account,
				"credit_in_account_currency": flt(self.amount),
			})

		je.remark = (
			f"Trust Transaction {self.name} - {self.transaction_type} - "
			f"{trust.trust_name}"
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

	def update_trust_balance(self):
		trust = frappe.get_doc("Perpetual Care Trust", self.perpetual_care_trust)
		trust.update_balance(self.amount, self.transaction_type)

	def revert_trust_balance(self):
		# Reverse the operation
		trust = frappe.get_doc("Perpetual Care Trust", self.perpetual_care_trust)
		reverse_map = {
			"Contribution": "Withdrawal",
			"Withdrawal": "Contribution",
			"Earnings": "Fee",
			"Fee": "Earnings",
		}
		reverse_type = reverse_map.get(self.transaction_type, self.transaction_type)
		trust.update_balance(self.amount, reverse_type)
