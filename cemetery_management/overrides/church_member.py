import frappe


def on_validate(doc, method):
    """Sync burial_plot from linked burial_record on Church Member."""
    if doc.get("burial_record"):
        burial_record = frappe.db.get_value(
            "Burial Record", doc.burial_record, "burial_plot"
        )
        if burial_record:
            doc.burial_plot = burial_record
    elif doc.get("burial_plot") and not doc.get("burial_record"):
        doc.burial_plot = None
