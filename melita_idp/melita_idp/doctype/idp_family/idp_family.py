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
		Він оновлює інформаційне поле family_summary та синхронізує дані з бенефіціарами.
		"""
		self.update_family_summary()
		self.sync_family_data_to_beneficiaries()

	def after_save(self):
		"""
		Виконується після збереження сім'ї.
		"""
		self.update_beneficiaries_family_reference()

	def update_family_summary(self):
		"""
		Оновлює поле family_summary на основі поточного складу сім'ї.
		"""
		# Перевіряємо, чи є взагалі члени в таблиці сім'ї
		if not self.family_members:
			self.family_summary = "Сім'я порожня"
			return

		# Знаходимо голову сім'ї
		head_of_family = None
		for member in self.family_members:
			if member.relationship == "Голова":
				head_of_family = member
				break

		if not head_of_family:
			# Якщо немає голови, беремо першого члена
			head_of_family = self.family_members[0]

		# Отримуємо повне ім'я голови сім'ї з бази даних
		try:
			head_full_name = frappe.db.get_value("IDP Beneficiary", head_of_family.member, "full_name")
			if not head_full_name:
				head_full_name = head_of_family.member
		except Exception:
			head_full_name = "Невідомий член сім'ї"

		# Рахуємо загальну кількість членів сім'ї
		member_count = len(self.family_members)

		# Формуємо фінальний рядок
		self.family_summary = f"{head_full_name} ({member_count} осіб)"

	def sync_family_data_to_beneficiaries(self):
		"""
		Синхронізує спільні дані сім'ї (адреси, дати переміщення) з усіма членами сім'ї.
		"""
		if not self.family_members:
			return

		# Отримуємо дані голови сім'ї для синхронізації
		head_data = None
		for member in self.family_members:
			if member.relationship == "Голова":
				try:
					head_data = frappe.get_doc("IDP Beneficiary", member.member)
					break
				except Exception:
					continue

		# Якщо голова не знайдена, беремо першого члена
		if not head_data and self.family_members:
			try:
				head_data = frappe.get_doc("IDP Beneficiary", self.family_members[0].member)
			except Exception:
				return

		if not head_data:
			return

		# Синхронізуємо дані для всіх членів сім'ї (крім голови)
		for member in self.family_members:
			if member.relationship != "Голова":
				try:
					self.sync_member_data(member.member, head_data)
				except Exception as e:
					frappe.log_error(f"Помилка синхронізації даних для {member.member}: {e!s}")

	def sync_member_data(self, member_id, head_data):
		"""
		Синхронізує спільні дані з головою сім'ї для конкретного члена.
		"""
		sync_fields = {
			"origin_region": self.origin_address or head_data.origin_region,
			"current_region": self.current_address or head_data.current_region,
			"current_address": head_data.current_address,
			"displacement_date": head_data.displacement_date,
			"displacement_status": head_data.displacement_status,
			"registration_center": head_data.registration_center,
			"idp_family": self.name,
		}

		# Оновлюємо поля тільки якщо вони не заповнені або відрізняються
		for field, value in sync_fields.items():
			if value:
				frappe.db.set_value("IDP Beneficiary", member_id, field, value, update_modified=False)

	def update_beneficiaries_family_reference(self):
		"""
		Оновлює посилання на сім'ю у всіх бенефіціарів.
		"""
		for member in self.family_members:
			try:
				current_family = frappe.db.get_value("IDP Beneficiary", member.member, "idp_family")
				if current_family != self.name:
					frappe.db.set_value(
						"IDP Beneficiary", member.member, "idp_family", self.name, update_modified=False
					)
			except Exception as e:
				frappe.log_error(f"Помилка оновлення посилання на сім'ю для {member.member}: {e!s}")

	def get_family_head(self):
		"""
		Повертає ID голови сім'ї.
		"""
		for member in self.family_members:
			if member.relationship == "Голова":
				return member.member
		return None

	def add_family_member(self, member_id, relationship="Член сім'ї"):
		"""
		Додає нового члена до сім'ї.
		"""
		# Перевіряємо, чи не є вже членом сім'ї
		existing_member = False
		for member in self.family_members:
			if member.member == member_id:
				existing_member = True
				break

		if not existing_member:
			self.append("family_members", {"member": member_id, "relationship": relationship})
			return True
		return False

	def remove_family_member(self, member_id):
		"""
		Видаляє члена з сім'ї.
		"""
		for i, member in enumerate(self.family_members):
			if member.member == member_id:
				self.family_members.pop(i)
				# Очищаємо посилання на сім'ю у бенефіціара
				frappe.db.set_value("IDP Beneficiary", member_id, "idp_family", "", update_modified=False)
				return True
		return False


@frappe.whitelist()
def get_family_head(family_id):
	"""
	API метод для отримання голови сім'ї.
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)
		return family_doc.get_family_head()
	except Exception as e:
		frappe.throw(f"Помилка при отриманні голови сім'ї: {e!s}")


@frappe.whitelist()
def add_member_to_family(family_id, member_id, relationship):
	"""
	API метод для додавання члена до сім'ї.
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)
		if family_doc.add_family_member(member_id, relationship):
			family_doc.save()
			return {"success": True, "message": f"Член сім'ї доданий як {relationship}"}
		else:
			return {"success": False, "message": "Цей бенефіціар вже є членом сім'ї"}
	except Exception as e:
		frappe.throw(f"Помилка при додаванні члена сім'ї: {e!s}")


@frappe.whitelist()
def remove_member_from_family(family_id, member_id):
	"""
	API метод для видалення члена з сім'ї.
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)
		if family_doc.remove_family_member(member_id):
			family_doc.save()
			return {"success": True, "message": "Член сім'ї видалений"}
		else:
			return {"success": False, "message": "Член сім'ї не знайдений"}
	except Exception as e:
		frappe.throw(f"Помилка при видаленні члена сім'ї: {e!s}")
