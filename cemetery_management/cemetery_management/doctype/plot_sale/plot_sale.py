# Copyright (c) 2026, Pleasant Springs Church and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PlotSale(Document):
	def validate(self):
		self.compute_perpetual_care()

	def compute_perpetual_care(self):
		settings = frappe.get_single("Cemetery Settings")
		pct = flt(settings.perpetual_care_percent)
		self.perpetual_care_amount = flt(self.amount) * pct / 100
		if settings.perpetual_care_account:
			self.perpetual_care_account = settings.perpetual_care_account

	def on_submit(self):
		self.create_journal_entry()
		if flt(self.perpetual_care_amount) > 0:
			self.create_perpetual_care_entry()
		self.update_plot_status()

	def on_cancel(self):
		self.cancel_journal_entries()
		self.revert_plot_status()

	def create_journal_entry(self):
		if self.journal_entry:
			return

		fee_type = frappe.get_doc("Cemetery Fee Type", self.cemetery_fee_type)

		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.sale_date
		je.company = self.company
		je.voucher_type = "Journal Entry"

		je.append("accounts", {
			"account": fee_type.debit_account,
			"debit_in_account_currency": flt(self.amount),
		})
		je.append("accounts", {
			"account": fee_type.income_account,
			"credit_in_account_currency": flt(self.amount),
		})

		je.remark = f"Plot Sale {self.name} - {self.buyer_name} - Plot {self.burial_plot}"
		je.insert(ignore_permissions=True)
		je.submit()

		self.db_set("journal_entry", je.name)

	def create_perpetual_care_entry(self):
		if self.perpetual_care_journal_entry:
			return
		if not self.perpetual_care_account:
			return

		fee_type = frappe.get_doc("Cemetery Fee Type", self.cemetery_fee_type)

		je = frappe.new_doc("Journal Entry")
		je.posting_date = self.sale_date
		je.company = self.company
		je.voucher_type = "Journal Entry"

		je.append("accounts", {
			"account": fee_type.income_account,
			"debit_in_account_currency": flt(self.perpetual_care_amount),
		})
		je.append("accounts", {
			"account": self.perpetual_care_account,
			"credit_in_account_currency": flt(self.perpetual_care_amount),
		})

		je.remark = f"Perpetual Care - Plot Sale {self.name} - Plot {self.burial_plot}"
		je.insert(ignore_permissions=True)
		je.submit()

		self.db_set("perpetual_care_journal_entry", je.name)

	def cancel_journal_entries(self):
		for field in ["journal_entry", "perpetual_care_journal_entry"]:
			je_name = self.get(field)
			if je_name:
				je = frappe.get_doc("Journal Entry", je_name)
				if je.docstatus == 1:
					je.cancel()
				self.db_set(field, None)

	def update_plot_status(self):
		if self.burial_plot:
			frappe.db.set_value("Burial Plot", self.burial_plot, "status", "Reserved")
			frappe.db.set_value("Burial Plot", self.burial_plot, "plot_owner", self.plot_owner)
			frappe.db.set_value("Burial Plot", self.burial_plot, "deed_number", self.payment_reference)
			frappe.db.set_value("Burial Plot", self.burial_plot, "purchase_date", self.sale_date)
			frappe.db.set_value("Burial Plot", self.burial_plot, "purchase_amount", self.amount)

	def revert_plot_status(self):
		if self.burial_plot:
			frappe.db.set_value("Burial Plot", self.burial_plot, "status", "Available")
