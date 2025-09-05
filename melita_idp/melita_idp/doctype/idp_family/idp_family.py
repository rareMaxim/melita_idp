# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IDPFamily(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from melita_idp.melita_idp.doctype.idp_family_member_item.idp_family_member_item import (
			IDPFamilyMemberItem,
		)

		current_address: DF.Link | None
		family_members: DF.Table[IDPFamilyMemberItem]
		family_summary: DF.Data | None
		origin_address: DF.Link | None
	# end: auto-generated types

	def before_save(self):
		"""
		Цей метод виконується автоматично перед кожним збереженням документа "Сім'я ВПО".
		Він оновлює інформаційне поле family_summary.
		"""
		self.update_family_summary()

	def update_family_summary(self):
		# Перевіряємо, чи є взагалі члени в таблиці сім'ї
		if not self.family_members:
			self.family_summary = "Сім'я порожня"
			return

		# Визначаємо "голову сім'ї" як першого члена у списку
		# self.family_members[0].member - це ID бенефіціара (напр. "ВПО-00001")
		head_of_family_id = self.family_members[0].member

		# Отримуємо повне ім'я цього бенефіціара з бази даних
		try:
			head_full_name = frappe.db.get_value("IDP Beneficiary", head_of_family_id, "full_name")
		except Exception:
			head_full_name = "Невідомий член сім'ї"

		# Рахуємо загальну кількість членів сім'ї
		member_count = len(self.family_members)

		# Формуємо фінальний рядок і записуємо його в наше нове поле
		self.family_summary = f"{head_full_name} ({member_count} осіб)"
