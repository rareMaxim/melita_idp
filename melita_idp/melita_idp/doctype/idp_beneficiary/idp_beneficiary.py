# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt


from datetime import date, timedelta

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
		first_name: DF.Data | None
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
		last_name: DF.Data | None
		last_visit_date: DF.Date | None
		middle_name: DF.Data | None
		origin_region: DF.Link | None
		personal_data_consent: DF.Check
		phone: DF.Data | None
		photo: DF.AttachImage | None
		professional_activity_sphere: DF.Data | None
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
		self.sync_family_address_if_head()

	def after_insert(self):
		"""Виконується після створення нового запису."""
		# Якщо це новий бенефіціар і у нього ще немає сім'ї, створюємо нову
		if not self.idp_family:
			self.create_family_and_add_as_head()

	def update_full_name(self):
		parsed_name = parse_full_name(self.full_name)
		self.last_name = parsed_name.get("last_name", "")
		self.first_name = parsed_name.get("first_name", "")
		self.middle_name = parsed_name.get("patronymic", "")

	def update_age(self):
		if self.date_of_birth:
			age = calculate_age(self.date_of_birth)
			self.age = age
		else:
			self.age = 0

	def sync_family_address_if_head(self):
		"""Синхронізує адресу сім'ї, якщо поточний бенефіціар є головою сім'ї."""
		if not self.idp_family:
			return

		try:
			family_doc = frappe.get_doc("IDP Family", self.idp_family)

			# Find if this beneficiary is the head
			is_head = any(
				member.member == self.name and member.relationship == "Голова"
				for member in family_doc.family_members
			)

			if is_head:
				updates = {}
				if self.origin_region != family_doc.origin_address:
					updates["origin_address"] = self.origin_region
				if self.current_region != family_doc.current_address:
					updates["current_address"] = self.current_region

				if updates:
					frappe.db.set_value("IDP Family", family_doc.name, updates)
		except Exception as e:
			frappe.log_error(f"Помилка синхронізації змін бенефіціара {self.name}: {e!s}")

	def create_family_and_add_as_head(self):
		"""Створює нову сім'ю ВПО та додає поточного бенефіціара як голову сім'ї."""
		try:
			family_doc = frappe.new_doc("IDP Family")
			family_doc.origin_address = self.origin_region
			family_doc.current_address = self.current_region
			family_doc.append("family_members", {"member": self.name, "relationship": "Голова"})
			family_doc.insert(ignore_permissions=True)
			frappe.db.set_value(
				"IDP Beneficiary", self.name, "idp_family", family_doc.name, update_modified=False
			)
			self.idp_family = family_doc.name
			frappe.msgprint(f"Автоматично створена сім'я: {family_doc.name}")
		except Exception as e:
			frappe.log_error(f"Помилка при створенні сім'ї для {self.name}: {e!s}")


def update_beneficiary():
	"""
	Масово оновлює дані бенефіціарів (вік та дані з РНОКПП), використовуючи пакетні оновлення.
	"""
	beneficiaries = frappe.get_all(
		"IDP Beneficiary", fields=["name", "date_of_birth", "tax_id", "gender", "age"]
	)

	# OPTIMIZATION: Prepare a dictionary for bulk_update, not a list.
	# The format is: { "doc_name_1": {"field_to_update": "value"}, "doc_name_2": {...} }
	updates_to_perform = {}

	for ben in beneficiaries:
		fields_to_update = {}

		# 1. Update from Tax ID (РНОКПП)
		if ben.tax_id:
			info = get_info_from_rnokpp(ben.tax_id)
			if "error" not in info:
				# Update date of birth if it's missing
				if not ben.date_of_birth and (dob := info.get("birth_date")):
					fields_to_update["date_of_birth"] = dob
					ben.date_of_birth = dob  # Use this new value for age calculation

				# Update gender if it's different
				if (gender := info.get("gender")) and gender != ben.gender:
					fields_to_update["gender"] = gender

		# 2. Update age if date of birth exists
		if ben.date_of_birth:
			age = calculate_age(ben.date_of_birth)
			if ben.age != age:
				fields_to_update["age"] = age

		# Add to the main dictionary only if there are actual changes
		if fields_to_update:
			updates_to_perform[ben.name] = fields_to_update

	# Perform all database updates in a single bulk operation if there's anything to update
	if updates_to_perform:
		frappe.db.bulk_update("IDP Beneficiary", updates_to_perform)
		frappe.log(f"Оновлено {len(updates_to_perform)} бенефіціарів.")
	else:
		frappe.log("Не знайдено бенефіціарів, що потребують оновлення.")


def calculate_age(birthdate):
	"""Розраховує повний вік людини."""
	if not birthdate:
		return 0
	birthdate = getdate(birthdate)
	today_date = getdate(today())
	# This calculation is correct and efficient.
	age = (
		today_date.year
		- birthdate.year
		- ((today_date.month, today_date.day) < (birthdate.month, birthdate.day))
	)
	return age


def get_info_from_rnokpp(rnokpp: str) -> dict:
	"""
	Отримує стать та дату народження з РНОКПП.

	Args:
	        rnokpp: Реєстраційний номер облікової картки платника податків (10-значний рядок).

	Returns:
	        Словник з ключами 'birth_date' (дата народження) та 'gender' (стать),
	        або повідомлення про помилку.
	"""
	if not rnokpp.isdigit() or len(rnokpp) != 10:
		return {"error": "РНОКПП повинен складатися з 10 цифр."}

	try:
		# Визначення дати народження
		days_offset = int(rnokpp[:5])
		base_date = date(1899, 12, 31)
		birth_date = base_date + timedelta(days=days_offset)

		# Визначення статі
		gender_digit = int(rnokpp[8])
		gender = "Чоловіча" if gender_digit % 2 != 0 else "Жіноча"

		return {"birth_date": birth_date.strftime("%Y-%m-%d"), "gender": gender}
	except ValueError:
		return {"error": "Некоректний формат РНОКПП."}


def parse_full_name(full_name: str | None) -> dict[str, str]:
	"""
	Розділяє повне ім'я на прізвище, ім'я та по батькові.

	Функція безпечно обробляє порожні рядки, None, а також випадки,
	коли по батькові відсутнє.

	Args:
	        full_name: Рядок, що містить повне ім'я (наприклад, "Шевченко Тарас Григорович").

	Returns:
	        Словник з ключами 'last_name', 'first_name', 'patronymic'.
	        Наприклад:
	        {
	                'last_name': 'Шевченко',
	                'first_name': 'Тарас',
	                'patronymic': 'Григорович'
	        }
	"""
	# 1. Попередньо ініціалізуємо результат з порожніми значеннями
	name_parts = {"last_name": "", "first_name": "", "patronymic": ""}

	# 2. Перевіряємо, чи вхідний рядок не є порожнім або None
	if not full_name or not full_name.strip():
		return name_parts

	# 3. Розділяємо рядок на слова по пробілах
	parts = full_name.strip().split()

	# 4. Розподіляємо частини імені залежно від їх кількості
	if len(parts) == 1:
		# Якщо є тільки одне слово, вважаємо його ім'ям
		name_parts["first_name"] = parts[0]
	elif len(parts) == 2:
		# Якщо два слова - це прізвище та ім'я
		name_parts["last_name"] = parts[0]
		name_parts["first_name"] = parts[1]
	elif len(parts) >= 3:
		# Якщо три або більше слів - це прізвище, ім'я та по батькові
		name_parts["last_name"] = parts[0]
		name_parts["first_name"] = parts[1]
		name_parts["patronymic"] = parts[2]

	return name_parts


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
