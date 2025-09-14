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
	"""
	try:
		family_doc = frappe.new_doc("IDP Family")
		family_doc.origin_address = beneficiary_doc.origin_region
		family_doc.current_address = beneficiary_doc.current_region
		family_doc.append("family_members", {"member": beneficiary_doc.name, "relationship": "Голова"})
		family_doc.insert(ignore_permissions=True)
		return family_doc.name
	except Exception as e:
		frappe.log_error(f"Помилка при створенні сім'ї для {beneficiary_doc.name}: {e!s}")
		return None


def sync_family_addresses(family_id, origin_address=None, current_address=None):
	"""
	Синхронізує адреси сім'ї з усіма її членами.
	"""
	try:
		family_doc = frappe.get_doc("IDP Family", family_id)
		if origin_address:
			family_doc.origin_address = origin_address
		if current_address:
			family_doc.current_address = current_address
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
	Повертає статистику сім'ї.
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
				if beneficiary.age:
					if beneficiary.age < 18:
						stats["children"] += 1
					elif beneficiary.age >= 65:
						stats["elderly"] += 1
					else:
						stats["adults"] += 1
				if beneficiary.gender == "Чоловіча":
					stats["males"] += 1
				elif beneficiary.gender == "Жіноча":
					stats["females"] += 1
				stats["relationships"][member.relationship] = (
					stats["relationships"].get(member.relationship, 0) + 1
				)
			except Exception:
				continue
		return stats
	except Exception as e:
		frappe.log_error(f"Помилка при отриманні статистики сім'ї {family_id}: {e!s}")
		return {}


def validate_family_relationships(family_doc):
	"""
	Валідує коректність ролей у сім'ї.
	"""
	errors = []
	heads_count = sum(1 for member in family_doc.family_members if member.relationship == "Голова")
	if heads_count == 0 and family_doc.family_members:
		errors.append("Сім'я повинна мати голову сім'ї")
	elif heads_count > 1:
		errors.append("Сім'я може мати тільки одного голову сім'ї")
	members = [m.member for m in family_doc.family_members]
	if len(members) != len(set(members)):
		errors.append("Знайдено дублікати бенефіціарів у сім'ї")
	return errors


def handle_beneficiary_rename(doc, method, old_name, new_name, merge=False):
	"""
	Хук для обробки перейменування бенефіціара.
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
	"""
	if doc.idp_family:
		try:
			family_doc = frappe.get_doc("IDP Family", doc.idp_family)
			family_doc.family_members = [m for m in family_doc.family_members if m.member != doc.name]
			if not family_doc.family_members:
				frappe.delete_doc("IDP Family", doc.idp_family, ignore_permissions=True)
			else:
				if not any(m.relationship == "Голова" for m in family_doc.family_members):
					family_doc.family_members[0].relationship = "Голова"
				family_doc.save(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Помилка обробки видалення бенефіціара {doc.name}: {e!s}")


def handle_family_update(doc, method):
	"""
	Хук для обробки оновлення сім'ї.
	"""
	for member in doc.family_members:
		if frappe.db.get_value("IDP Beneficiary", member.member, "idp_family") != doc.name:
			frappe.db.set_value(
				"IDP Beneficiary", member.member, "idp_family", doc.name, update_modified=False
			)


def handle_family_deletion(doc, method):
	"""
	Хук для обробки видалення сім'ї.
	"""
	for member in doc.family_members:
		frappe.db.set_value("IDP Beneficiary", member.member, "idp_family", "", update_modified=False)


def validate_family_structure_hook(doc, method):
	"""
	Хук валідації структури сім'ї.
	"""
	errors = validate_family_relationships(doc)
	if errors:
		frappe.throw(f"Помилки структури сім'ї: {'; '.join(errors)}")


def cleanup_empty_families():
	"""
	Планувальник: Очищає порожні сім'ї.
	"""
	empty_families = frappe.get_all("IDP Family", filters={"family_members": ("<=", 0)})
	for family in empty_families:
		frappe.delete_doc("IDP Family", family.name, ignore_permissions=True)
	if empty_families:
		frappe.db.commit()


@frappe.whitelist()
def transfer_beneficiary_to_family(beneficiary_id, target_family_id, relationship):
	"""
	Переводить бенефіціара з однієї сім'ї до іншої з вказаною роллю.
	"""
	try:
		beneficiary = frappe.get_doc("IDP Beneficiary", beneficiary_id)
		current_family_id = beneficiary.idp_family
		was_head = False

		# 1. Видаляємо бенефіціара з поточної сім'ї
		if current_family_id:
			current_family = frappe.get_doc("IDP Family", current_family_id)
			member_to_remove = next(
				(m for m in current_family.family_members if m.member == beneficiary_id), None
			)

			if member_to_remove:
				was_head = member_to_remove.relationship == "Голова"
				current_family.remove(member_to_remove)

				if not current_family.family_members:
					frappe.delete_doc("IDP Family", current_family.name, ignore_permissions=True)
				else:
					if was_head and not any(
						m.relationship == "Голова" for m in current_family.family_members
					):
						current_family.family_members[0].relationship = "Голова"
					current_family.save(ignore_permissions=True)

		# 2. Додаємо бенефіціара до нової сім'ї
		target_family = frappe.get_doc("IDP Family", target_family_id)
		if any(m.member == beneficiary_id for m in target_family.family_members):
			return {"success": False, "message": "Бенефіціар вже є членом цієї сім'ї."}

		new_relationship = relationship
		target_has_head = any(m.relationship == "Голова" for m in target_family.family_members)

		if was_head and target_has_head:
			new_relationship = "Інший родич"
		elif was_head and not target_has_head:
			new_relationship = "Голова"
		elif relationship == "Голова" and target_has_head:
			frappe.throw("Цільова сім'я вже має голову. Будь ласка, оберіть іншу роль.")

		target_family.append("family_members", {"member": beneficiary_id, "relationship": new_relationship})
		target_family.save(ignore_permissions=True)

		frappe.db.set_value("IDP Beneficiary", beneficiary_id, "idp_family", target_family_id)
		return {"success": True, "message": "Бенефіціар переведений до нової сім'ї"}

	except Exception as e:
		frappe.log_error(frappe.get_traceback())
		frappe.throw(f"Помилка переведення бенефіціара: {e!s}")
