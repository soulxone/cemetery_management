import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def bulk_create_plots(
	cemetery,
	section,
	row_start,
	row_end,
	plot_start,
	plot_end,
	plot_type="Standard",
	status="Available",
	max_interments=1,
):
	"""
	Bulk-create burial plots for a given cemetery section.

	Args:
		cemetery: Cemetery name
		section: Section identifier (e.g. "A", "B", "Veterans")
		row_start/row_end: Row range (inclusive)
		plot_start/plot_end: Plot number range (inclusive)
		plot_type: Plot type (Standard, Companion, Family, Cremation, etc.)
		status: Initial status (Available, Unavailable)
		max_interments: Maximum interments per plot

	Returns:
		dict with created count and skipped count
	"""
	if not frappe.db.exists("Cemetery", cemetery):
		frappe.throw(_("Cemetery {0} does not exist").format(cemetery))

	row_start = cint(row_start)
	row_end = cint(row_end)
	plot_start = cint(plot_start)
	plot_end = cint(plot_end)

	if row_start > row_end:
		frappe.throw(_("Row Start must be less than or equal to Row End"))
	if plot_start > plot_end:
		frappe.throw(_("Plot Start must be less than or equal to Plot End"))

	# Get cemetery abbreviation for naming
	cemetery_name = frappe.db.get_value("Cemetery", cemetery, "cemetery_name")
	words = cemetery_name.split() if cemetery_name else ["CEM"]
	if len(words) >= 2:
		abbr = (words[0][0] + words[1][0]).upper()
	else:
		abbr = words[0][:3].upper()

	created = 0
	skipped = 0

	for row in range(row_start, row_end + 1):
		for plot_num in range(plot_start, plot_end + 1):
			row_str = str(row)
			plot_str = str(plot_num)

			# Check for existing plot
			expected_name = f"PLT-{abbr}-{section}-{row_str}-{plot_str}"
			if frappe.db.exists("Burial Plot", expected_name):
				skipped += 1
				continue

			doc = frappe.new_doc("Burial Plot")
			doc.cemetery = cemetery
			doc.section = section
			doc.row = row_str
			doc.plot_number = plot_str
			doc.plot_type = plot_type
			doc.status = status
			doc.max_interments = cint(max_interments) or 1
			doc.flags.ignore_mandatory = True
			doc.insert(ignore_permissions=True)
			created += 1

	frappe.db.commit()

	return {
		"created": created,
		"skipped": skipped,
		"total_range": (row_end - row_start + 1) * (plot_end - plot_start + 1),
	}
