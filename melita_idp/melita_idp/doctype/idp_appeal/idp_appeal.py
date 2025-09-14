# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

import frappe
import frappe.utils
from frappe.model.document import Document
from frappe.utils.data import date_diff, getdate


class IDPAppeal(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		applicant: DF.Link
		date: DF.Date
		family: DF.Link | None
		photo: DF.AttachImage | None
		service_category: DF.Link | None
		service_name: DF.Link | None
		support_center: DF.Link
	# end: auto-generated types

	def before_save(self):
		if self.applicant:
			applicant_last_visit_date = frappe.get_value("IDP Beneficiary", self.applicant, "last_visit_date")

			# Use getdate() to convert the string to a date object for comparison
			if applicant_last_visit_date is None or date_diff(self.date, applicant_last_visit_date) > 0:
				frappe.set_value("IDP Beneficiary", self.applicant, "last_visit_date", self.date)


@frappe.whitelist()
def get_appeal_heatmap_data(name, doctype):
	"""
	Повертає дані для теплової карти звернень у структурі, аналогічній get_timeline_data.
	"""
	if doctype != "IDP Beneficiary":
		return {"timeline_data": {}}

	# Отримуємо дані про звернення
	appeal_data = frappe.get_all(
		"IDP Appeal",
		fields=["date", "count(name) as count"],
		filters={"applicant": name},
		group_by="date",
		order_by="date",
	)

	# Форматуємо дані у вигляд timestamp: count
	timeline_data = {}
	for entry in appeal_data:
		timeline_data[frappe.utils.get_timestamp(entry.date)] = entry.count

	# Повертаємо результат у вказаному форматі
	return {"timeline_data": timeline_data}
