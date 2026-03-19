import frappe

no_cache = 1


def get_context(context):
    context.page_title = "Cemetery Search - Pleasant Springs Cemetery"
    context.no_breadcrumbs = True

    if frappe.db.exists("Cemetery", "Pleasant Springs Cemetery"):
        context.cemetery = frappe.get_doc("Cemetery", "Pleasant Springs Cemetery")
    else:
        context.cemetery = None

    return context


@frappe.whitelist(allow_guest=True)
def search_burials(query="", birth_year="", death_year="", veteran_only=""):
    """Public API for searching burial records."""
    filters = {"docstatus": 1}
    or_filters = []

    if query:
        query = query.strip()
        or_filters = [
            ["full_name", "like", f"%{query}%"],
            ["maiden_name", "like", f"%{query}%"],
        ]

    if birth_year:
        try:
            year = int(birth_year)
            filters["date_of_birth"] = [">=", f"{year}-01-01"]
            filters["date_of_birth"] = ["<=", f"{year}-12-31"]
        except ValueError:
            pass

    if death_year:
        try:
            year = int(death_year)
            filters["date_of_death"] = ["between", [f"{year}-01-01", f"{year}-12-31"]]
        except ValueError:
            pass

    if veteran_only == "1":
        filters["is_veteran"] = 1

    results = frappe.get_all(
        "Burial Record",
        filters=filters,
        or_filters=or_filters if or_filters else None,
        fields=[
            "name", "full_name", "maiden_name",
            "date_of_birth", "date_of_death", "age_at_death",
            "burial_plot", "cemetery", "primary_photo",
            "is_veteran", "military_branch",
            "findagrave_url", "interment_type",
        ],
        order_by="last_name asc, first_name asc",
        limit=200,
    )

    return results
