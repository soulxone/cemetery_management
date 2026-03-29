import frappe
from frappe.utils import flt, add_months, getdate, today


def execute(filters=None):
	columns = [
		{"fieldname": "month", "label": "Month", "fieldtype": "Data", "width": 150},
		{"fieldname": "expected_payments", "label": "Expected Contract Payments", "fieldtype": "Currency", "width": 200},
		{"fieldname": "contracts_due", "label": "Contracts Due", "fieldtype": "Int", "width": 120},
	]

	# Get all active pre-need contracts with balance remaining
	contracts = frappe.get_all(
		"Pre-Need Contract",
		filters={"docstatus": 1, "contract_status": "Active"},
		fields=["name", "installment_amount", "balance_remaining",
				"payment_frequency", "next_payment_due"],
	)

	frequency_months = {
		"Monthly": 1,
		"Quarterly": 3,
		"Semi-Annual": 6,
		"Annual": 12,
		"Lump Sum": 0,
	}

	# Project 12 months forward
	data = []
	base_date = getdate(today())

	for i in range(12):
		month_start = add_months(base_date, i)
		month_label = month_start.strftime("%B %Y")
		month_total = 0
		month_count = 0

		for c in contracts:
			if not c.next_payment_due or flt(c.balance_remaining) <= 0:
				continue

			freq = frequency_months.get(c.payment_frequency, 1)
			if freq == 0:
				continue

			due = getdate(c.next_payment_due)
			# Check if a payment falls in this month
			check_date = due
			while check_date <= add_months(month_start, 1):
				if (check_date.year == month_start.year and
					check_date.month == month_start.month):
					month_total += flt(c.installment_amount)
					month_count += 1
					break
				check_date = add_months(check_date, freq)

		data.append({
			"month": month_label,
			"expected_payments": month_total,
			"contracts_due": month_count,
		})

	return columns, data
