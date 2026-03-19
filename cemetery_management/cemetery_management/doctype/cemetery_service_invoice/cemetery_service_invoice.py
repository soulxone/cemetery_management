# Copyright (c) 2026, Pleasant Springs Church and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CemeteryServiceInvoice(Document):
	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		total = 0
		for item in self.services:
			item.amount = flt(item.quantity) * flt(item.rate)
			total += flt(item.amount)
		self.total_amount = total

	def on_submit(self):
		self.create_journal_entry()

	def on_cancel(self):
		if self.journal_entry:
			je = frappe.get_doc("Journal Entry", self.journal_entry)
			if je.docstatus == 1:
				je.cancel()
			self.db_set("journal_entry", None)

	def create_journal_entry(self):
		if self.journal_entry:
			return

		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.invoice_date
		je.company = self.company
		je.voucher_type = "Journal Entry"

		for item in self.services:
			if not item.amount:
				continue
			fee_type = frappe.get_doc("Cemetery Fee Type", item.cemetery_fee_type)
			je.append("accounts", {
				"account": fee_type.debit_account,
				"debit_in_account_currency": flt(item.amount),
			})
			je.append("accounts", {
				"account": fee_type.income_account,
				"credit_in_account_currency": flt(item.amount),
			})

		je.remark = f"Cemetery Service Invoice {self.name} - {self.customer_name}"
		je.insert(ignore_permissions=True)
		je.submit()

		self.db_set("journal_entry", je.name)
