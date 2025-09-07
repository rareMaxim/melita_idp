# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

"""
Утиліти для роботи з сім'ями ВПО.
Цей файл має бути розміщений за шляхом: melita_idp/melita_idp/utils/family_utils.py
"""

import frappe
from frappe.utils import getdate, today


def create_family_for_beneficiary(beneficiary_doc):
	"""
	Створює нову сім'ю для бенефіціара та додає його як голову сім'ї.

	Args:
	        beneficiary_doc: Документ IDP Beneficiary

	Returns:
	        str: ID створеної сім'ї або None у випадку помилки
	"""
	try:
		# Створюємо новий документ сім'ї
		family_doc = frappe.new_doc("IDP Family")

		# Заповнюємо базові дані сім'ї
		family_doc.origin_address = beneficiary_doc.origin_region
		family_doc.current_address = beneficiary_doc.current_region

		# Додаємо поточного бенефіціара як голову сім'ї
		family_doc.append("family_members", {"member": beneficiary_doc.name, "relationship": "Голова"})

		# Зберігаємо сім'ю
		family_doc.insert(ignore_permissions=True)

		return family_doc.name

	except Exception as e:
		frappe.log_error(f"Помилка при створенні сім'ї для {beneficiary_doc.name}: {e!s}")
		return None


def sync_family_addresses(family_id, origin_address=None, current_address=None):
	"""
	Синхронізує адреси сім'ї з усіма її членами.

	Args:
	        family_id: ID сім'ї
	        origin_address: Нова адреса походження (опціонально)
	        current_address: Нова поточна адреса (опціонально)
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)

		if origin_address:
			family_doc.origin_address = origin_address
		if current_address:
			family_doc.current_address = current_address

		# Оновлюємо адреси для всіх членів сім'ї
		for member in family_doc.family_members:
			update_data = {}
			if origin_address:
				update_data["origin_region"] = origin_address
			if current_address:
				update_data["current_region"] = current_address

			if update_data:
				frappe.db.set_value("IDP Beneficiary", member.member, update_data, update_modified=False)

		family_doc.save()

	except Exception as e:
		frappe.log_error(f"Помилка синхронізації адрес для сім'ї {family_id}: {e!s}")


def get_family_statistics(family_id):
	"""
	Повертає статистику сім'ї (кількість членів, вікові групи, тощо).

	Args:
	        family_id: ID сім'ї

	Returns:
	        dict: Словник зі статистикою сім'ї
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)

		stats = {
			"total_members": len(family_doc.family_members),
			"adults": 0,
			"children": 0,
			"elderly": 0,
			"males": 0,
			"females": 0,
			"relationships": {},
		}

		for member in family_doc.family_members:
			try:
				beneficiary = frappe.get_doc("IDP Beneficiary", member.member)

				# Підраховуємо за віком
				if beneficiary.age:
					if beneficiary.age < 18:
						stats["children"] += 1
					elif beneficiary.age >= 65:
						stats["elderly"] += 1
					else:
						stats["adults"] += 1

				# Підраховуємо за статтю
				if beneficiary.gender == "Чоловіча":
					stats["males"] += 1
				elif beneficiary.gender == "Жіноча":
					stats["females"] += 1

				# Підраховуємо за ролями в сім'ї
				if member.relationship in stats["relationships"]:
					stats["relationships"][member.relationship] += 1
				else:
					stats["relationships"][member.relationship] = 1

			except Exception:
				continue

		return stats

	except Exception as e:
		frappe.log_error(f"Помилка при отриманні статистики сім'ї {family_id}: {e!s}")
		return {}


def validate_family_relationships(family_doc):
	"""
	Валідує коректність ролей у сім'ї.

	Args:
	        family_doc: Документ IDP Family

	Returns:
	        list: Список помилок валідації
	"""
	errors = []

	# Перевіряємо наявність голови сім'ї
	heads_count = sum(1 for member in family_doc.family_members if member.relationship == "Голова")

	if heads_count == 0:
		errors.append("Сім'я повинна мати голову сім'ї")
	elif heads_count > 1:
		errors.append("Сім'я може мати тільки одного голову сім'ї")

	# Перевіряємо унікальність членів
	members_set = set()
	for member in family_doc.family_members:
		if member.member in members_set:
			errors.append(f"Бенефіціар {member.member} вже доданий до сім'ї")
		members_set.add(member.member)

	return errors


def merge_families(primary_family_id, secondary_family_id):
	"""
	Об'єднує дві сім'ї в одну.

	Args:
	        primary_family_id: ID основної сім'ї (залишається)
	        secondary_family_id: ID сім'ї, яка об'єднується (видаляється)

	Returns:
	        bool: True якщо успішно, False якщо помилка
	"""
	try:
		primary_family = frappe.get_doc("IDP Family", primary_family_id)
		secondary_family = frappe.get_doc("IDP Family", secondary_family_id)

		# Переносимо всіх членів з другорядної сім'ї
		for member in secondary_family.family_members:
			# Перевіряємо, чи не є вже членом основної сім'ї
			already_exists = any(m.member == member.member for m in primary_family.family_members)

			if not already_exists:
				# Змінюємо роль якщо це голова другорядної сім'ї
				relationship = "Член сім'ї" if member.relationship == "Голова" else member.relationship

				primary_family.append(
					"family_members", {"member": member.member, "relationship": relationship}
				)

		# Зберігаємо основну сім'ю
		primary_family.save()

		# Видаляємо другорядну сім'ю
		frappe.delete_doc("IDP Family", secondary_family_id)

		return True

	except Exception as e:
		frappe.log_error(f"Помилка при об'єднанні сімей {primary_family_id} та {secondary_family_id}: {e!s}")
		return False


def split_family_member(family_id, member_id):
	"""
	Виділяє члена сім'ї в окрему сім'ю.

	Args:
	        family_id: ID поточної сім'ї
	        member_id: ID члена, який виділяється

	Returns:
	        str: ID нової сім'ї або None у випадку помилки
	"""
	try:
		current_family = frappe.get_doc("IDP Family", family_id)
		member_doc = frappe.get_doc("IDP Beneficiary", member_id)

		# Видаляємо члена з поточної сім'ї
		for i, member in enumerate(current_family.family_members):
			if member.member == member_id:
				current_family.family_members.pop(i)
				break

		# Зберігаємо зміни в поточній сім'ї
		current_family.save()

		# Створюємо нову сім'ю для цього члена
		new_family_id = create_family_for_beneficiary(member_doc)

		if new_family_id:
			# Оновлюємо посилання на сім'ю у бенефіціара
			frappe.db.set_value(
				"IDP Beneficiary", member_id, "idp_family", new_family_id, update_modified=False
			)

		return new_family_id

	except Exception as e:
		frappe.log_error(f"Помилка при виділенні члена {member_id} з сім'ї {family_id}: {e!s}")
		return None


@frappe.whitelist()
def get_available_beneficiaries_for_family(family_id=None):
	"""
	Повертає список бенефіціарів, які можуть бути додані до сім'ї.

	Args:
	        family_id: ID сім'ї (для виключення поточних членів)

	Returns:
	        list: Список доступних бенефіціарів
	"""
	try:
		# Базовий запит
		filters = {"status": ["!=", "Помер"]}

		# Якщо передана сім'я, виключаємо її поточних членів
		if family_id:
			family_doc = frappe.get_doc("IDP Family", family_id)
			current_members = [member.member for member in family_doc.family_members]
			if current_members:
				filters["name"] = ["not in", current_members]

		beneficiaries = frappe.get_all(
			"IDP Beneficiary",
			filters=filters,
			fields=["name", "full_name", "phone", "age", "gender", "idp_family"],
			order_by="full_name",
		)

		return beneficiaries

	except Exception as e:
		frappe.log_error(f"Помилка при отриманні доступних бенефіціарів: {e!s}")
		return []


# Хук-функції для автоматичної обробки подій


def handle_beneficiary_rename(doc, method, old_name, new_name, merge=False):
	"""
	Хук для обробки перейменування бенефіціара.
	Оновлює посилання в сім'ї.
	"""
	if doc.idp_family:
		try:
			family_doc = frappe.get_doc("IDP Family", doc.idp_family)

			for member in family_doc.family_members:
				if member.member == old_name:
					member.member = new_name
					break

			family_doc.save()

		except Exception as e:
			frappe.log_error(f"Помилка оновлення посилань при перейменуванні {old_name} -> {new_name}: {e!s}")


def handle_beneficiary_deletion(doc, method):
	"""
	Хук для обробки видалення бенефіціара.
	Видаляє його з сім'ї.
	"""
	if doc.idp_family:
		try:
			family_doc = frappe.get_doc("IDP Family", doc.idp_family)

			# Видаляємо з сім'ї
			for i, member in enumerate(family_doc.family_members):
				if member.member == doc.name:
					family_doc.family_members.pop(i)
					break

			# Якщо сім'я стала порожньою, видаляємо її
			if not family_doc.family_members:
				frappe.delete_doc("IDP Family", doc.idp_family)
			else:
				# Якщо видалили голову сім'ї, призначаємо нового
				if doc.is_family_head() and family_doc.family_members:
					family_doc.family_members[0].relationship = "Голова"

				family_doc.save()

		except Exception as e:
			frappe.log_error(f"Помилка обробки видалення бенефіціара {doc.name}: {e!s}")


def handle_family_update(doc, method):
	"""
	Хук для обробки оновлення сім'ї.
	"""
	try:
		# Валідуємо структуру сім'ї
		errors = validate_family_relationships(doc)
		if errors:
			frappe.throw(f"Помилки валідації сім'ї: {'; '.join(errors)}")

		# Оновлюємо посилання на сім'ю у всіх членів
		for member in doc.family_members:
			current_family = frappe.db.get_value("IDP Beneficiary", member.member, "idp_family")
			if current_family != doc.name:
				frappe.db.set_value(
					"IDP Beneficiary", member.member, "idp_family", doc.name, update_modified=False
				)

	except Exception as e:
		frappe.log_error(f"Помилка обробки оновлення сім'ї {doc.name}: {e!s}")


def handle_family_deletion(doc, method):
	"""
	Хук для обробки видалення сім'ї.
	Очищає посилання у бенефіціарів.
	"""
	try:
		for member in doc.family_members:
			frappe.db.set_value("IDP Beneficiary", member.member, "idp_family", "", update_modified=False)

	except Exception as e:
		frappe.log_error(f"Помилка обробки видалення сім'ї {doc.name}: {e!s}")


def validate_family_structure_hook(doc, method):
	"""
	Хук валідації структури сім'ї.
	"""
	errors = validate_family_relationships(doc)
	if errors:
		frappe.throw(f"Помилки структури сім'ї: {'; '.join(errors)}")


def cleanup_empty_families():
	"""
	Планувальник: Очищає порожні сім'ї (без членів).
	"""
	try:
		empty_families = frappe.get_all(
			"IDP Family", fields=["name"], filters={"family_members": ["is", "not set"]}
		)

		for family in empty_families:
			frappe.delete_doc("IDP Family", family.name)
			frappe.log_error(f"Видалена порожня сім'я: {family.name}")

		if empty_families:
			frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Помилка очищення порожніх сімей: {e!s}")


# Додаткові API методи


@frappe.whitelist()
def transfer_beneficiary_to_family(beneficiary_id, target_family_id, relationship="Член сім'ї"):
	"""
	Переводить бенефіціара з однієї сім'ї до іншої.
	"""
	try:
		beneficiary = frappe.get_doc("IDP Beneficiary", beneficiary_id)

		# Видаляємо з поточної сім'ї
		if beneficiary.idp_family:
			current_family = frappe.get_doc("IDP Family", beneficiary.idp_family)
			current_family.remove_family_member(beneficiary_id)
			current_family.save()

		# Додаємо до нової сім'ї
		target_family = frappe.get_doc("IDP Family", target_family_id)
		target_family.add_family_member(beneficiary_id, relationship)
		target_family.save()

		return {"success": True, "message": "Бенефіціар переведений до нової сім'ї"}

	except Exception as e:
		frappe.throw(f"Помилка переведення бенефіціара: {e!s}")


@frappe.whitelist()
def get_family_report_data(family_id):
	"""
	Повертає детальні дані сім'ї для звітів.
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)

		report_data = {
			"family_info": {
				"name": family_doc.name,
				"summary": family_doc.family_summary,
				"origin_address": family_doc.origin_address,
				"current_address": family_doc.current_address,
				"creation": family_doc.creation,
				"modified": family_doc.modified,
			},
			"members": [],
			"statistics": get_family_statistics(family_id),
		}

		for member in family_doc.family_members:
			try:
				beneficiary = frappe.get_doc("IDP Beneficiary", member.member)
				report_data["members"].append(
					{
						"id": beneficiary.name,
						"full_name": beneficiary.full_name,
						"relationship": member.relationship,
						"phone": beneficiary.phone,
						"age": beneficiary.age,
						"gender": beneficiary.gender,
						"date_of_birth": beneficiary.date_of_birth,
						"status": beneficiary.status,
						"registration_date": beneficiary.registration_date,
					}
				)
			except Exception:
				continue

		return report_data

	except Exception as e:
		frappe.throw(f"Помилка формування звіту по сім'ї: {e!s}")


@frappe.whitelist()
def bulk_update_family_addresses(family_ids, origin_address=None, current_address=None):
	"""
	Масове оновлення адрес для кількох сімей.
	"""
	try:
		if isinstance(family_ids, str):
			family_ids = frappe.parse_json(family_ids)

		updated_count = 0

		for family_id in family_ids:
			try:
				sync_family_addresses(family_id, origin_address, current_address)
				updated_count += 1
			except Exception:
				continue

		return {"success": True, "message": f"Оновлено адреси для {updated_count} сімей з {len(family_ids)}"}

	except Exception as e:
		frappe.throw(f"Помилка масового оновлення адрес: {e!s}")
