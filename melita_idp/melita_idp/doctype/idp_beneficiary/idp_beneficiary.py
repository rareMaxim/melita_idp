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
		self.update_age()
		if self.idp_family and self.is_family_head():
			try:
				family_doc = frappe.get_doc("IDP Family", self.idp_family)
				# Оновлюємо адреси сім'ї
				if self.origin_region != family_doc.origin_address:
					family_doc.origin_address = self.origin_region
				if self.current_region != family_doc.current_address:
					family_doc.current_address = self.current_region
				family_doc.save()
			except Exception as e:
				frappe.log_error(f"Помилка синхронізації змін бенефіціара {self.name}: {e!s}")

	def after_insert(self):
		"""Виконується після створення нового запису."""
		# Якщо це новий бенефіціар і у нього ще немає сім'ї, створюємо нову
		if not self.idp_family:
			self.create_family_and_add_as_head()

	def update_full_name(self):
		self.full_name = f"{self.last_name or ''} {self.first_name or ''} {self.middle_name or ''}".strip()

	def update_age(self):
		if self.date_of_birth:
			age = calculate_age(self.date_of_birth)
			self.age = age
		else:
			self.age = 0

	def create_family_and_add_as_head(self):
		"""Створює нову сім'ю ВПО та додає поточного бенефіціара як голову сім'ї."""
		try:
			# Створюємо новий документ сім'ї
			family_doc = frappe.new_doc("IDP Family")

			# Заповнюємо базові дані сім'ї
			family_doc.origin_address = self.origin_region
			family_doc.current_address = self.current_region

			# Додаємо поточного бенефіціара як голову сім'ї
			family_doc.append("family_members", {"member": self.name, "relationship": "Голова"})

			# Зберігаємо сім'ю
			family_doc.insert(ignore_permissions=True)

			# Оновлюємо поле idp_family у поточного бенефіціара
			frappe.db.set_value(
				"IDP Beneficiary", self.name, "idp_family", family_doc.name, update_modified=False
			)

			# Оновлюємо також поточний об'єкт
			self.idp_family = family_doc.name

			frappe.msgprint(f"Автоматично створена сім'я: {family_doc.name}")

		except Exception as e:
			frappe.log_error(f"Помилка при створенні сім'ї для {self.name}: {e!s}")

	def get_family_head(self):
		"""Повертає голову сім'ї для поточного бенефіціара."""
		if not self.idp_family:
			return None

		# Знаходимо голову сім'ї
		family_doc = frappe.get_doc("IDP Family", self.idp_family)
		for member in family_doc.family_members:
			if member.relationship == "Голова":
				return member.member
		return None

	def is_family_head(self):
		"""Перевіряє, чи є поточний бенефіціар головою сім'ї."""
		family_head = self.get_family_head()
		return family_head == self.name if family_head else False


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


@frappe.whitelist()
def add_family_member(family_id, origin_beneficiary_id):
	"""
	Повертає дані для створення нового члена сім'ї з заповненими спільними полями.
	"""
	try:
		# Отримуємо дані сім'ї
		family_doc = frappe.get_doc("IDP Family", family_id)
		origin_beneficiary = frappe.get_doc("IDP Beneficiary", origin_beneficiary_id)

		# Підготовлюємо дані для нового бенефіціара
		shared_data = {
			"origin_region": family_doc.origin_address,
			"current_region": family_doc.current_address,
			"current_address": origin_beneficiary.current_address,
			"displacement_date": origin_beneficiary.displacement_date,
			"displacement_status": origin_beneficiary.displacement_status,
			"registration_center": origin_beneficiary.registration_center,
			"idp_family": family_id,
			"temp_relationship": "Член сім'ї",  # Тимчасове поле для збереження ролі
		}

		return shared_data

	except Exception as e:
		frappe.throw(f"Помилка при підготовці даних для нового члена сім'ї: {e!s}")


@frappe.whitelist()
def get_family_common_fields(family_id):
	"""
	Повертає спільні поля для членів сім'ї.
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)

		# Знаходимо голову сім'ї для отримання додаткових даних
		head_member = None
		for member in family_doc.family_members:
			if member.relationship == "Голова":
				head_member = frappe.get_doc("IDP Beneficiary", member.member)
				break

		common_fields = {
			"origin_region": family_doc.origin_address,
			"current_region": family_doc.current_address,
		}

		if head_member:
			common_fields.update(
				{
					"current_address": head_member.current_address,
					"displacement_date": head_member.displacement_date,
					"displacement_status": head_member.displacement_status,
					"registration_center": head_member.registration_center,
				}
			)

		return common_fields

	except Exception as e:
		frappe.throw(f"Помилка при отриманні спільних полів сім'ї: {e!s}")


@frappe.whitelist()
def get_family_members_data(family_id):
	"""
	Безпечно повертає дані про членів сім'ї для клієнтського скрипту.
	"""
	if not family_id:
		return []

	try:
		family_doc = frappe.get_doc("IDP Family", family_id)
		if not family_doc.family_members:
			return []

		member_names = [member.member for member in family_doc.family_members]
		if not member_names:
			return []

		# Отримуємо дані всіх членів одним запитом
		member_details = frappe.get_all(
			"IDP Beneficiary",
			filters={"name": ("in", member_names)},
			fields=["name", "full_name", "phone", "age", "gender"],
		)
		member_map = {doc.name: doc for doc in member_details}

		# Формуємо фінальний список з усіма даними
		family_data = []
		for member_link in family_doc.family_members:
			details = member_map.get(member_link.member)
			if details:
				family_data.append(
					{
						"name": details.name,
						"full_name": details.full_name,
						"relationship": member_link.relationship,
						"phone": details.phone,
						"age": details.age,
						"gender": details.gender,
					}
				)
		return family_data
	except Exception as e:
		frappe.log_error(f"Помилка в get_family_members_data для сім'ї {family_id}: {e!s}")
		return {"error": str(e)}
