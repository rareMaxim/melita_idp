# Адміністративні утиліти для управління сім'ями ВПО

"""
Цей файл містить утиліти для адміністрування та обслуговування системи сімей ВПО.
Розмістіть як: melita_idp/melita_idp/utils/admin_utils.py
"""

import frappe
from frappe import _
from frappe.utils import cstr, getdate, today


def check_system_integrity():
	"""
	Перевіряє цілісність системи сімей ВПО і повертає звіт про проблеми.
	"""
	issues = []

	try:
		# 1. Перевіряємо бенефіціарів без сімей
		orphaned_beneficiaries = frappe.db.sql(
			"""
			SELECT name, full_name
			FROM `tabIDP Beneficiary`
			WHERE (idp_family IS NULL OR idp_family = '')
			AND status != 'Помер'
		""",
			as_dict=True,
		)

		if orphaned_beneficiaries:
			issues.append(
				{
					"type": "orphaned_beneficiaries",
					"count": len(orphaned_beneficiaries),
					"message": f"Знайдено {len(orphaned_beneficiaries)} бенефіціарів без сімей",
					"data": orphaned_beneficiaries,
				}
			)

		# 2. Перевіряємо сім'ї без голови
		families_without_head = frappe.db.sql(
			"""
			SELECT f.name, f.family_summary
			FROM `tabIDP Family` f
			LEFT JOIN `tabIDP Family Member Item` m
				ON m.parent = f.name AND m.relationship = 'Голова'
			WHERE m.name IS NULL
		""",
			as_dict=True,
		)

		if families_without_head:
			issues.append(
				{
					"type": "families_without_head",
					"count": len(families_without_head),
					"message": f"Знайдено {len(families_without_head)} сімей без голови",
					"data": families_without_head,
				}
			)

		# 3. Перевіряємо сім'ї з кількома головами
		families_multiple_heads = frappe.db.sql(
			"""
			SELECT f.name, f.family_summary, COUNT(m.name) as head_count
			FROM `tabIDP Family` f
			JOIN `tabIDP Family Member Item` m
				ON m.parent = f.name AND m.relationship = 'Голова'
			GROUP BY f.name
			HAVING COUNT(m.name) > 1
		""",
			as_dict=True,
		)

		if families_multiple_heads:
			issues.append(
				{
					"type": "families_multiple_heads",
					"count": len(families_multiple_heads),
					"message": f"Знайдено {len(families_multiple_heads)} сімей з кількома головами",
					"data": families_multiple_heads,
				}
			)

		# 4. Перевіряємо невідповідності посилань
		broken_references = frappe.db.sql(
			"""
			SELECT b.name as beneficiary, b.idp_family, m.parent as actual_family
			FROM `tabIDP Beneficiary` b
			LEFT JOIN `tabIDP Family Member Item` m
				ON m.member = b.name
			WHERE b.idp_family IS NOT NULL
			AND b.idp_family != ''
			AND (m.parent IS NULL OR b.idp_family != m.parent)
		""",
			as_dict=True,
		)

		if broken_references:
			issues.append(
				{
					"type": "broken_references",
					"count": len(broken_references),
					"message": f"Знайдено {len(broken_references)} невідповідностей посилань",
					"data": broken_references,
				}
			)

		# 5. Порожні сім'ї
		empty_families = frappe.db.sql(
			"""
			SELECT f.name, f.family_summary
			FROM `tabIDP Family` f
			LEFT JOIN `tabIDP Family Member Item` m ON m.parent = f.name
			WHERE m.name IS NULL
		""",
			as_dict=True,
		)

		if empty_families:
			issues.append(
				{
					"type": "empty_families",
					"count": len(empty_families),
					"message": f"Знайдено {len(empty_families)} порожніх сімей",
					"data": empty_families,
				}
			)

		return {
			"success": True,
			"issues_found": len(issues) > 0,
			"total_issues": sum(issue["count"] for issue in issues),
			"issues": issues,
		}

	except Exception as e:
		return {"success": False, "error": str(e), "issues": []}


def fix_orphaned_beneficiaries(auto_fix=False):
	"""
	Виправляє бенефіціарів без сімей, створюючи для них нові сім'ї.

	Args:
	        auto_fix (bool): Якщо True, автоматично виправляє проблеми
	"""
	try:
		orphaned = frappe.db.sql(
			"""
			SELECT name, full_name, origin_region, current_region
			FROM `tabIDP Beneficiary`
			WHERE (idp_family IS NULL OR idp_family = '')
			AND status != 'Помер'
		""",
			as_dict=True,
		)

		if not orphaned:
			return {"success": True, "message": "Бенефіціарів без сімей не знайдено", "fixed": 0}

		if not auto_fix:
			return {
				"success": True,
				"message": f"Знайдено {len(orphaned)} бенефіціарів без сімей. Для автоматичного виправлення передайте auto_fix=True",
				"count": len(orphaned),
				"preview": orphaned[:5],  # Показуємо перші 5 для перегляду
			}

		fixed_count = 0

		for beneficiary in orphaned:
			try:
				# Створюємо нову сім'ю
				family_doc = frappe.new_doc("IDP Family")
				family_doc.origin_address = beneficiary.get("origin_region")
				family_doc.current_address = beneficiary.get("current_region")

				# Додаємо бенефіціара як голову сім'ї
				family_doc.append("family_members", {"member": beneficiary["name"], "relationship": "Голова"})

				family_doc.insert(ignore_permissions=True)

				# Оновлюємо посилання у бенефіціара
				frappe.db.set_value("IDP Beneficiary", beneficiary["name"], "idp_family", family_doc.name)

				fixed_count += 1

			except Exception as e:
				frappe.log_error(f"Помилка створення сім'ї для {beneficiary['name']}: {e!s}")

		frappe.db.commit()

		return {
			"success": True,
			"message": f"Створено сім'ї для {fixed_count} з {len(orphaned)} бенефіціарів",
			"fixed": fixed_count,
			"total": len(orphaned),
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


def fix_families_without_head(auto_fix=False):
	"""
	Виправляє сім'ї без голови, призначаючи першого члена головою.
	"""
	try:
		families = frappe.db.sql(
			"""
			SELECT f.name, f.family_summary
			FROM `tabIDP Family` f
			LEFT JOIN `tabIDP Family Member Item` m
				ON m.parent = f.name AND m.relationship = 'Голова'
			WHERE m.name IS NULL
		""",
			as_dict=True,
		)

		if not families:
			return {"success": True, "message": "Сімей без голови не знайдено", "fixed": 0}

		if not auto_fix:
			return {
				"success": True,
				"message": f"Знайдено {len(families)} сімей без голови. Для виправлення передайте auto_fix=True",
				"count": len(families),
				"preview": families[:5],
			}

		fixed_count = 0

		for family in families:
			try:
				family_doc = frappe.get_doc("IDP Family", family["name"])

				if family_doc.family_members:
					# Призначаємо першого члена головою
					family_doc.family_members[0].relationship = "Голова"
					family_doc.save()
					fixed_count += 1
				else:
					# Видаляємо порожню сім'ю
					frappe.delete_doc("IDP Family", family["name"])

			except Exception as e:
				frappe.log_error(f"Помилка виправлення сім'ї {family['name']}: {e!s}")

		frappe.db.commit()

		return {"success": True, "message": f"Виправлено {fixed_count} сімей", "fixed": fixed_count}

	except Exception as e:
		return {"success": False, "error": str(e)}


def cleanup_broken_references(auto_fix=False):
	"""
	Очищає невідповідності між посиланнями на сім'ї у бенефіціарів та фактичним членством.
	"""
	try:
		broken = frappe.db.sql(
			"""
			SELECT b.name as beneficiary, b.idp_family, m.parent as actual_family
			FROM `tabIDP Beneficiary` b
			LEFT JOIN `tabIDP Family Member Item` m
				ON m.member = b.name
			WHERE b.idp_family IS NOT NULL
			AND b.idp_family != ''
			AND (m.parent IS NULL OR b.idp_family != m.parent)
		""",
			as_dict=True,
		)

		if not broken:
			return {"success": True, "message": "Невідповідностей не знайдено", "fixed": 0}

		if not auto_fix:
			return {
				"success": True,
				"message": f"Знайдено {len(broken)} невідповідностей. Для виправлення передайте auto_fix=True",
				"count": len(broken),
				"preview": broken[:5],
			}

		fixed_count = 0

		for ref in broken:
			try:
				if ref.get("actual_family"):
					# Оновлюємо посилання у бенефіціара на фактичну сім'ю
					frappe.db.set_value(
						"IDP Beneficiary", ref["beneficiary"], "idp_family", ref["actual_family"]
					)
				else:
					# Очищаємо невірне посилання
					frappe.db.set_value("IDP Beneficiary", ref["beneficiary"], "idp_family", "")

				fixed_count += 1

			except Exception as e:
				frappe.log_error(f"Помилка виправлення посилання для {ref['beneficiary']}: {e!s}")

		frappe.db.commit()

		return {
			"success": True,
			"message": f"Виправлено {fixed_count} невідповідностей",
			"fixed": fixed_count,
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


def generate_family_report():
	"""
	Генерує загальний звіт по всіх сім'ях у системі.
	"""
	try:
		# Загальна статистика
		total_families = frappe.db.count("IDP Family")
		total_beneficiaries = frappe.db.count("IDP Beneficiary", {"status": ["!=", "Помер"]})

		# Розподіл за розміром сім'ї
		family_sizes = frappe.db.sql(
			"""
			SELECT
				CASE
					WHEN member_count = 1 THEN '1 особа'
					WHEN member_count BETWEEN 2 AND 3 THEN '2-3 особи'
					WHEN member_count BETWEEN 4 AND 5 THEN '4-5 осіб'
					WHEN member_count >= 6 THEN '6+ осіб'
				END as size_group,
				COUNT(*) as family_count
			FROM (
				SELECT f.name, COUNT(m.member) as member_count
				FROM `tabIDP Family` f
				LEFT JOIN `tabIDP Family Member Item` m ON m.parent = f.name
				GROUP BY f.name
			) as family_stats
			GROUP BY size_group
			ORDER BY MIN(member_count)
		""",
			as_dict=True,
		)

		# Топ регіонів за кількістю сімей
		top_regions = frappe.db.sql(
			"""
			SELECT
				COALESCE(k.region_name, f.origin_address, 'Не вказано') as region,
				COUNT(f.name) as family_count
			FROM `tabIDP Family` f
			LEFT JOIN `tabKATOTTG` k ON k.name = f.origin_address
			GROUP BY f.origin_address
			ORDER BY COUNT(f.name) DESC
			LIMIT 10
		""",
			as_dict=True,
		)

		# Статистика за віком голів сімей
		head_age_stats = frappe.db.sql(
			"""
			SELECT
				CASE
					WHEN b.age < 25 THEN 'До 25 років'
					WHEN b.age BETWEEN 25 AND 35 THEN '25-35 років'
					WHEN b.age BETWEEN 36 AND 50 THEN '36-50 років'
					WHEN b.age BETWEEN 51 AND 65 THEN '51-65 років'
					WHEN b.age > 65 THEN 'Старше 65 років'
					ELSE 'Вік не вказано'
				END as age_group,
				COUNT(*) as count
			FROM `tabIDP Beneficiary` b
			JOIN `tabIDP Family Member Item` m ON m.member = b.name AND m.relationship = 'Голова'
			GROUP BY age_group
			ORDER BY MIN(COALESCE(b.age, 0))
		""",
			as_dict=True,
		)

		# Статистика за статтю голів сімей
		head_gender_stats = frappe.db.sql(
			"""
			SELECT
				COALESCE(b.gender, 'Не вказано') as gender,
				COUNT(*) as count
			FROM `tabIDP Beneficiary` b
			JOIN `tabIDP Family Member Item` m ON m.member = b.name AND m.relationship = 'Голова'
			GROUP BY b.gender
		""",
			as_dict=True,
		)

		# Сім'ї з дітьми
		families_with_children = frappe.db.sql("""
			SELECT COUNT(DISTINCT f.name) as count
			FROM `tabIDP Family` f
			JOIN `tabIDP Family Member Item` m ON m.parent = f.name
			JOIN `tabIDP Beneficiary` b ON b.name = m.member
			WHERE b.age < 18
		""")[0][0]

		report = {
			"generated_at": frappe.utils.now(),
			"summary": {
				"total_families": total_families,
				"total_beneficiaries": total_beneficiaries,
				"families_with_children": families_with_children,
				"average_family_size": round(total_beneficiaries / total_families, 2)
				if total_families > 0
				else 0,
			},
			"family_sizes": family_sizes,
			"top_regions": top_regions,
			"head_demographics": {
				"age_distribution": head_age_stats,
				"gender_distribution": head_gender_stats,
			},
		}

		return {"success": True, "report": report}

	except Exception as e:
		return {"success": False, "error": str(e)}


def export_families_to_excel(filters=None):
	"""
	Експортує дані сімей у Excel файл.

	Args:
	        filters (dict): Фільтри для вибірки сімей
	"""
	try:
		# Базовий запит
		where_conditions = ["1=1"]

		if filters:
			if filters.get("origin_region"):
				where_conditions.append(f"f.origin_address = '{filters['origin_region']}'")
			if filters.get("min_members"):
				where_conditions.append(f"member_count >= {filters['min_members']}")
			if filters.get("max_members"):
				where_conditions.append(f"member_count <= {filters['max_members']}")

		where_clause = " AND ".join(where_conditions)

		# Основні дані сімей
		families_data = frappe.db.sql(
			f"""
			SELECT
				f.name as family_id,
				f.family_summary,
				f.origin_address,
				f.current_address,
				f.creation,
				f.modified,
				COUNT(m.member) as member_count,
				GROUP_CONCAT(
					CONCAT(b.full_name, ' (', m.relationship, ')')
					ORDER BY CASE WHEN m.relationship = 'Голова' THEN 1 ELSE 2 END
					SEPARATOR '; '
				) as members_list
			FROM `tabIDP Family` f
			LEFT JOIN `tabIDP Family Member Item` m ON m.parent = f.name
			LEFT JOIN `tabIDP Beneficiary` b ON b.name = m.member
			GROUP BY f.name
			HAVING {where_clause}
			ORDER BY f.creation DESC
		""",
			as_dict=True,
		)

		# Створюємо Excel файл (тут потрібна бібліотека openpyxl або xlwt)
		# Для простоти повертаємо дані у форматі, готовому для експорту

		export_data = {
			"families": families_data,
			"summary": {
				"total_exported": len(families_data),
				"export_date": frappe.utils.now(),
				"filters_applied": filters or {},
			},
		}

		return {"success": True, "data": export_data}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def run_system_maintenance():
	"""
	Запускає повне обслуговування системи сімей.
	"""
	try:
		maintenance_log = []

		# 1. Перевірка цілісності
		integrity_check = check_system_integrity()
		maintenance_log.append({"step": "integrity_check", "result": integrity_check})

		if integrity_check.get("issues_found"):
			# 2. Виправлення бенефіціарів без сімей
			orphaned_fix = fix_orphaned_beneficiaries(auto_fix=True)
			maintenance_log.append({"step": "fix_orphaned", "result": orphaned_fix})

			# 3. Виправлення сімей без голови
			headless_fix = fix_families_without_head(auto_fix=True)
			maintenance_log.append({"step": "fix_headless", "result": headless_fix})

			# 4. Очищення невідповідностей
			references_fix = cleanup_broken_references(auto_fix=True)
			maintenance_log.append({"step": "fix_references", "result": references_fix})

		# 5. Оновлення віку всіх бенефіціарів
		from melita_idp.melita_idp.doctype.idp_beneficiary.idp_beneficiary import update_beneficiary_age

		update_beneficiary_age()
		maintenance_log.append(
			{"step": "update_ages", "result": {"success": True, "message": "Вік оновлено"}}
		)

		# 6. Очищення порожніх сімей
		from melita_idp.melita_idp.utils.family_utils import cleanup_empty_families

		cleanup_empty_families()
		maintenance_log.append(
			{"step": "cleanup_empty", "result": {"success": True, "message": "Порожні сім'ї очищено"}}
		)

		return {
			"success": True,
			"message": "Обслуговування системи завершено",
			"maintenance_log": maintenance_log,
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e),
			"maintenance_log": maintenance_log if "maintenance_log" in locals() else [],
		}


@frappe.whitelist()
def get_system_statistics():
	"""
	Повертає детальну статистику системи сімей.
	"""
	try:
		stats = {
			"families": {
				"total": frappe.db.count("IDP Family"),
				"with_children": frappe.db.sql("""
					SELECT COUNT(DISTINCT f.name)
					FROM `tabIDP Family` f
					JOIN `tabIDP Family Member Item` m ON m.parent = f.name
					JOIN `tabIDP Beneficiary` b ON b.name = m.member
					WHERE b.age < 18
				""")[0][0],
				"single_person": frappe.db.sql("""
					SELECT COUNT(*)
					FROM (
						SELECT f.name
						FROM `tabIDP Family` f
						JOIN `tabIDP Family Member Item` m ON m.parent = f.name
						GROUP BY f.name
						HAVING COUNT(m.member) = 1
					) as single_families
				""")[0][0],
			},
			"beneficiaries": {
				"total": frappe.db.count("IDP Beneficiary", {"status": ["!=", "Помер"]}),
				"children": frappe.db.count("IDP Beneficiary", {"age": ["<", 18], "status": ["!=", "Помер"]}),
				"adults": frappe.db.count(
					"IDP Beneficiary", {"age": ["between", [18, 64]], "status": ["!=", "Помер"]}
				),
				"elderly": frappe.db.count("IDP Beneficiary", {"age": [">=", 65], "status": ["!=", "Помер"]}),
				"male": frappe.db.count("IDP Beneficiary", {"gender": "Чоловіча", "status": ["!=", "Помер"]}),
				"female": frappe.db.count("IDP Beneficiary", {"gender": "Жіноча", "status": ["!=", "Помер"]}),
			},
			"integrity": check_system_integrity(),
			"recent_activity": {
				"families_created_today": frappe.db.count(
					"IDP Family", {"creation": [">=", frappe.utils.today()]}
				),
				"beneficiaries_created_today": frappe.db.count(
					"IDP Beneficiary", {"creation": [">=", frappe.utils.today()]}
				),
				"last_maintenance": frappe.db.get_single_value("System Settings", "last_family_maintenance")
				or "Ніколи",
			},
		}

		return {"success": True, "statistics": stats}

	except Exception as e:
		return {"success": False, "error": str(e)}


# Консольні команди для bench


def console_check_integrity():
	"""Консольна команда для перевірки цілісності"""
	result = check_system_integrity()
	print("=== ПЕРЕВІРКА ЦІЛІСНОСТІ СИСТЕМИ ===")
	print(f"Успішно: {result['success']}")
	print(f"Проблеми знайдено: {result['issues_found']}")
	print(f"Всього проблем: {result.get('total_issues', 0)}")

	for issue in result.get("issues", []):
		print(f"\n{issue['type']}: {issue['message']}")
		if issue.get("data"):
			for item in issue["data"][:3]:  # Показуємо перші 3
				print(f"  - {item}")
			if len(issue["data"]) > 3:
				print(f"  ... і ще {len(issue['data']) - 3}")


def console_fix_all():
	"""Консольна команда для виправлення всіх проблем"""
	print("=== АВТОМАТИЧНЕ ВИПРАВЛЕННЯ ПРОБЛЕМ ===")

	result = run_system_maintenance()
	print(f"Успішно: {result['success']}")
	print(f"Повідомлення: {result.get('message', '')}")

	for step in result.get("maintenance_log", []):
		print(f"\n{step['step']}: {step['result'].get('message', 'Виконано')}")


# Ініціалізація
if __name__ == "__main__":
	# Для тестування в консолі
	console_check_integrity()
