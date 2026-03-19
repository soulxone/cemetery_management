import frappe


def execute(filters=None):
    columns = [
        {"fieldname": "cemetery", "label": "Cemetery", "fieldtype": "Link", "options": "Cemetery", "width": 200},
        {"fieldname": "section", "label": "Section", "fieldtype": "Data", "width": 150},
        {"fieldname": "total", "label": "Total Plots", "fieldtype": "Int", "width": 100},
        {"fieldname": "available", "label": "Available", "fieldtype": "Int", "width": 100},
        {"fieldname": "occupied", "label": "Occupied", "fieldtype": "Int", "width": 100},
        {"fieldname": "reserved", "label": "Reserved", "fieldtype": "Int", "width": 100},
        {"fieldname": "occupancy_pct", "label": "Occupancy %", "fieldtype": "Percent", "width": 120},
    ]

    conditions = ""
    if filters and filters.get("cemetery"):
        conditions = f"AND cemetery = {frappe.db.escape(filters['cemetery'])}"

    data = frappe.db.sql(f"""
        SELECT
            cemetery,
            COALESCE(NULLIF(section, ''), 'Unassigned') as section,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available,
            SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied,
            SUM(CASE WHEN status = 'Reserved' THEN 1 ELSE 0 END) as reserved,
            ROUND(SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as occupancy_pct
        FROM `tabBurial Plot`
        WHERE 1=1 {conditions}
        GROUP BY cemetery, COALESCE(NULLIF(section, ''), 'Unassigned')
        ORDER BY cemetery, section
    """, as_dict=True)

    return columns, data
