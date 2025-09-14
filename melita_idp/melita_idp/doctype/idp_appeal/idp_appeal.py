# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IDPAppeal(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		applicant: DF.Link | None
		date: DF.Date | None
		family: DF.Link | None
		photo: DF.AttachImage | None
		service_category: DF.Link | None
		service_name: DF.Link | None
		support_center: DF.Link | None
	# end: auto-generated types

	pass

	def before_update(self):
		if self.applicant:
			applicant_last_visit_date = frappe.get_value("IDP Beneficiary", self.applicant, "last_visit_date")
			if applicant_last_visit_date is None or self.date > applicant_last_visit_date:
				frappe.db.set_value("IDP Beneficiary", self.applicant, "last_visit_date", self.date)
