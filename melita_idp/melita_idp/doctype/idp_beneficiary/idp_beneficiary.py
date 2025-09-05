# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class IDPBeneficiary(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from melita_idp.melita_idp.doctype.idp_family_member_item.idp_family_member_item import (
			IDPFamilyMemberItem,
		)
		from melita_idp.melita_idp.doctype.idp_vulnerability_table.idp_vulnerability_table import (
			IDPVulnerabilityTable,
		)

		age: DF.Int
		contact_email: DF.Data | None
		current_address: DF.SmallText | None
		current_region: DF.Link | None
		date_of_birth: DF.Date | None
		death_date: DF.Date | None
		displacement_date: DF.Date | None
		displacement_status: DF.Literal[
			"\u041d\u0435\u0449\u043e\u0434\u0430\u0432\u043d\u043e \u043f\u0435\u0440\u0435\u043c\u0456\u0449\u0435\u043d\u0438\u0439",
			"\u0414\u043e\u0432\u0433\u043e\u0441\u0442\u0440\u043e\u043a\u043e\u0432\u043e \u043f\u0435\u0440\u0435\u043c\u0456\u0449\u0435\u043d\u0438\u0439",
			"\u041f\u043e\u0432\u0435\u0440\u043d\u0443\u0432\u0441\u044f",
		]
		document: DF.Data | None
		document_type: DF.Literal[
			"\u041f\u0430\u0441\u043f\u043e\u0440\u0442",
			"ID-\u043a\u0430\u0440\u0442\u043a\u0430",
			"\u0421\u0432\u0456\u0434\u043e\u0446\u0442\u0432\u043e \u043f\u0440\u043e \u043d\u0430\u0440\u043e\u0434\u0436\u0435\u043d\u043d\u044f",
			"\u0406\u043d\u0448\u0435",
		]
		education: DF.Literal[
			"\u041f\u043e\u0447\u0430\u0442\u043a\u043e\u0432\u0430",
			"\u0421\u0435\u0440\u0435\u0434\u043d\u044f",
			"\u0421\u0435\u0440\u0435\u0434\u043d\u044c\u043e-\u0441\u043f\u0435\u0446\u0456\u0430\u043b\u044c\u043d\u0430",
			"\u0412\u0438\u0449\u0430",
		]
		employment_status: DF.Literal[
			"\u041f\u0440\u0430\u0446\u0435\u0432\u043b\u0430\u0448\u0442\u043e\u0432\u0430\u043d\u0438\u0439",
			"\u0411\u0435\u0437\u0440\u043e\u0431\u0456\u0442\u043d\u0438\u0439",
			"\u0415\u043a\u043e\u043d\u043e\u043c\u0456\u0447\u043d\u043e \u043d\u0435\u0430\u043a\u0442\u0438\u0432\u043d\u0438\u0439",
		]
		family_members_display: DF.Table[IDPFamilyMemberItem]
		first_name: DF.Data
		full_name: DF.Data | None
		gender: DF.Literal[
			"", "\u0427\u043e\u043b\u043e\u0432\u0456\u0447\u0430", "\u0416\u0456\u043d\u043e\u0447\u0430"
		]
		health_status: DF.Literal[
			"\u0417\u0430\u0434\u043e\u0432\u0456\u043b\u044c\u043d\u0438\u0439",
			"\u041f\u043e\u0442\u0440\u0435\u0431\u0443\u0454 \u0434\u043e\u0433\u043b\u044f\u0434\u0443",
			"\u041b\u0435\u0436\u0430\u0447\u0438\u0439",
		]
		idp_certificate_number: DF.Data | None
		idp_family: DF.Link | None
		is_bedridden: DF.Check
		is_pregnant: DF.Check
		is_single_parent: DF.Check
		last_name: DF.Data
		last_visit_date: DF.Date | None
		middle_name: DF.Data
		origin_region: DF.Link | None
		personal_data_consent: DF.Check
		phone: DF.Data | None
		photo: DF.AttachImage | None
		professional_activity_sphere: DF.Link | None
		receives_vpo_allowance: DF.Check
		registration_center: DF.Link | None
		registration_date: DF.Date | None
		status: DF.Literal[
			"\u0410\u043a\u0442\u0438\u0432\u043d\u0438\u0439",
			"\u041f\u0435\u0440\u0435\u043c\u0456\u0441\u0442\u0438\u0432\u0441\u044f",
			"\u0417\u043d\u044f\u0442\u043e \u0437 \u043e\u0431\u043b\u0456\u043a\u0443",
			"\u041f\u043e\u043c\u0435\u0440",
		]
		tax_id: DF.Data | None
		temp_relationship: DF.Data | None
		vpo_certificate_date: DF.Date | None
		vulnerability_categories: DF.TableMultiSelect[IDPVulnerabilityTable]
	# end: auto-generated types

	def before_save(self):
		"""Виконується перед збереженням."""
		self.update_full_name()

	def update_full_name(self):
		self.full_name = f"{self.last_name or ''} {self.first_name or ''} {self.middle_name or ''}".strip()

	def update_age(self):
		if self.date_of_birth:
			age = calculate_age(self.date_of_birth)
			self.age = age
		else:
			self.age = 0


def update_beneficiary_age():
	beneficiaries = frappe.get_all("IDP Beneficiary", fields=["name", "date_of_birth"])
	for ben in beneficiaries:
		if ben.date_of_birth:
			age = calculate_age(ben.date_of_birth)
			frappe.db.set_value("IDP Beneficiary", ben.name, "age", age, update_modified=False)


def calculate_age(birthdate):
	birthdate = getdate(birthdate)
	today_date = getdate(today())
	age = (
		today_date.year
		- birthdate.year
		- ((today_date.month, today_date.day) < (birthdate.month, birthdate.day))
	)
	return age
