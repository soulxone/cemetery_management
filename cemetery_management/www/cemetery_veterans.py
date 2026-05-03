import frappe

no_cache = 1


def get_context(context):
	context.page_title = "Veterans Honor Roll | Pleasant Springs Cemetery, TN"
	context.title = context.page_title
	context.metatags = {
		"title": context.page_title,
		"description": "Honoring American veterans interred at Pleasant Springs Cemetery near Pinson, TN. Searchable by branch and conflict — Civil War through present.",
		"keywords": "veterans honor roll, military burials tennessee, civil war graves tn, pleasant springs cemetery veterans",
		"image": "https://ps-church.com/files/og-default.png",
		"og:type": "website",
		"og:title": "Veterans Honor Roll — Pleasant Springs Cemetery",
		"og:description": "Honoring American veterans interred at Pleasant Springs Cemetery near Pinson, Tennessee.",
		"og:image": "https://ps-church.com/files/og-default.png",
		"og:url": "https://ps-church.com/cemetery-veterans",
		"twitter:card": "summary_large_image",
	}
	context.no_breadcrumbs = True

	veterans = frappe.get_all(
		"Burial Record",
		filters={"docstatus": 1, "is_veteran": 1},
		fields=[
			"name", "full_name", "date_of_birth", "date_of_death",
			"military_branch", "military_rank", "military_war",
			"burial_plot", "primary_photo",
		],
		order_by="military_branch asc, last_name asc, first_name asc",
	)

	# Group by branch
	branches = {}
	for v in veterans:
		branch = v.military_branch or "Other"
		if branch not in branches:
			branches[branch] = []
		branches[branch].append(v)

	context.branches = branches
	context.total_veterans = len(veterans)

	return context
