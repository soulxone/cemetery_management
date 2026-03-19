# Copyright (c) 2026, Pleasant Springs Church and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BurialPlot(Document):
	def before_save(self):
		if self.cemetery and not self.cemetery_abbr:
			# Generate abbreviation from cemetery name
			name = self.cemetery or ""
			words = name.split()
			self.cemetery_abbr = "".join(w[0].upper() for w in words if w)[:4]
