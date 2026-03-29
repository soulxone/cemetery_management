import frappe


def execute(filters=None):
	columns = [
		{"fieldname": "decade", "label": "Decade of Death", "fieldtype": "Data", "width": 150},
		{"fieldname": "burial_count", "label": "Burials", "fieldtype": "Int", "width": 100},
		{"fieldname": "veterans", "label": "Veterans", "fieldtype": "Int", "width": 100},
		{"fieldname": "avg_age", "label": "Avg Age (years)", "fieldtype": "Float", "width": 130},
		{"fieldname": "youngest", "label": "Youngest", "fieldtype": "Int", "width": 100},
		{"fieldname": "oldest", "label": "Oldest", "fieldtype": "Int", "width": 100},
	]

	data = frappe.db.sql(
		"""
		SELECT
			CONCAT(FLOOR(YEAR(date_of_death) / 10) * 10, 's') as decade,
			COUNT(*) as burial_count,
			SUM(CASE WHEN is_veteran = 1 THEN 1 ELSE 0 END) as veterans,
			ROUND(AVG(
				YEAR(date_of_death) - YEAR(date_of_birth)
				- (DATE_FORMAT(date_of_death, '%%m%%d') < DATE_FORMAT(date_of_birth, '%%m%%d'))
			), 1) as avg_age,
			MIN(
				YEAR(date_of_death) - YEAR(date_of_birth)
				- (DATE_FORMAT(date_of_death, '%%m%%d') < DATE_FORMAT(date_of_birth, '%%m%%d'))
			) as youngest,
			MAX(
				YEAR(date_of_death) - YEAR(date_of_birth)
				- (DATE_FORMAT(date_of_death, '%%m%%d') < DATE_FORMAT(date_of_birth, '%%m%%d'))
			) as oldest
		FROM `tabBurial Record`
		WHERE docstatus = 1
			AND date_of_death IS NOT NULL
			AND date_of_birth IS NOT NULL
		GROUP BY FLOOR(YEAR(date_of_death) / 10) * 10
		ORDER BY FLOOR(YEAR(date_of_death) / 10) * 10
		""",
		as_dict=True,
	)

	return columns, data
