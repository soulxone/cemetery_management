import frappe

no_cache = 1


def get_context(context):
	burial_record = frappe.form_dict.get("burial_record")

	if not burial_record or not frappe.db.exists("Burial Record", burial_record):
		frappe.throw("Memorial not found", frappe.DoesNotExistError)

	record = frappe.get_doc("Burial Record", burial_record)

	# Only show submitted records
	if record.docstatus != 1:
		frappe.throw("Memorial not found", frappe.DoesNotExistError)

	context.record = record
	context.page_title = f"In Memory of {record.full_name}"
	context.no_breadcrumbs = True

	# Get photos
	context.photos = record.photos or []

	# Get approved tributes
	context.tributes = frappe.get_all(
		"Memorial Tribute",
		filters={"burial_record": burial_record, "is_approved": 1},
		fields=["tribute_by", "message", "submitted_date"],
		order_by="submitted_date desc",
		limit=50,
	)

	# Get plot GPS for mini-map
	context.has_map = False
	if record.burial_plot:
		plot = frappe.get_doc("Burial Plot", record.burial_plot)
		if plot.latitude and plot.longitude:
			context.has_map = True
			context.plot_lat = plot.latitude
			context.plot_lng = plot.longitude
		context.plot = plot
	else:
		context.plot = None

	return context


@frappe.whitelist(allow_guest=True)
def submit_tribute(burial_record, tribute_by, tribute_email="", message=""):
	"""Allow guests to submit a tribute for moderation."""
	if not burial_record or not frappe.db.exists("Burial Record", burial_record):
		frappe.throw("Invalid burial record")

	if not tribute_by or not message:
		frappe.throw("Name and message are required")

	# Verify it's a submitted record
	docstatus = frappe.db.get_value("Burial Record", burial_record, "docstatus")
	if docstatus != 1:
		frappe.throw("Invalid burial record")

	doc = frappe.new_doc("Memorial Tribute")
	doc.burial_record = burial_record
	doc.tribute_by = tribute_by.strip()
	doc.tribute_email = tribute_email.strip() if tribute_email else ""
	doc.message = message.strip()
	doc.is_approved = 0
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)

	return "Thank you. Your tribute will appear after review."
