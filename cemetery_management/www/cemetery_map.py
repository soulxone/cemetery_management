import frappe

no_cache = 1


def get_context(context):
	context.page_title = "Pleasant Springs Cemetery Map | Pinson, TN"
	context.title = context.page_title
	context.metatags = {
		"title": context.page_title,
		"description": "Interactive map of Pleasant Springs Cemetery near Pinson, Tennessee. Find burial plots, navigate the grounds, and locate ancestors.",
		"keywords": "pleasant springs cemetery map, cemetery plot map tennessee, find a grave map pinson tn",
		"image": "https://ps-church.com/files/og-default.png",
		"og:type": "website",
		"og:title": "Pleasant Springs Cemetery Map",
		"og:description": "Interactive map of burial plots and cemetery grounds near Pinson, Tennessee.",
		"og:image": "https://ps-church.com/files/og-default.png",
		"og:url": "https://ps-church.com/cemetery-map",
		"twitter:card": "summary_large_image",
	}
	context.no_breadcrumbs = True

	settings = frappe.get_single("Cemetery Settings")
	cemetery_name = settings.default_cemetery or "Pleasant Springs Cemetery"

	if frappe.db.exists("Cemetery", cemetery_name):
		cemetery = frappe.get_doc("Cemetery", cemetery_name)
		context.cemetery = cemetery
		context.center_lat = cemetery.latitude or 35.418182
		context.center_lng = cemetery.longitude or -88.790044
	else:
		context.cemetery = None
		context.center_lat = 35.418182
		context.center_lng = -88.790044

	return context


@frappe.whitelist(allow_guest=True)
def get_plot_markers():
	"""Return all burial plots with GPS coordinates for map display."""
	plots = frappe.db.sql(
		"""
		SELECT
			bp.name, bp.section, bp.row, bp.plot_number,
			bp.status, bp.plot_type, bp.latitude, bp.longitude,
			bp.current_interments, bp.max_interments,
			bp.has_monument, bp.monument_type,
			po.owner_name as plot_owner_name
		FROM `tabBurial Plot` bp
		LEFT JOIN `tabPlot Owner` po ON bp.plot_owner = po.name
		WHERE bp.latitude IS NOT NULL
			AND bp.longitude IS NOT NULL
			AND bp.latitude != 0
			AND bp.longitude != 0
		""",
		as_dict=True,
	)

	# Attach burial info for occupied plots
	for plot in plots:
		if plot.status == "Occupied" or plot.current_interments:
			burials = frappe.get_all(
				"Burial Record",
				filters={"burial_plot": plot.name, "docstatus": 1},
				fields=["name", "full_name", "date_of_birth", "date_of_death", "is_veteran", "military_branch"],
				order_by="interment_date desc",
				limit=3,
			)
			plot["burials"] = burials
		else:
			plot["burials"] = []

	return plots
