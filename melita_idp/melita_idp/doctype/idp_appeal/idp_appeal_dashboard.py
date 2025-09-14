import frappe
import frappe.utils
from frappe import _


@frappe.whitelist()
def get_appeal_heatmap_data(docname, doctype):
	"""
	Повертає дані для теплової карти звернень для вказаного документа.
	"""
	filters = {}
	if doctype == "IDP Beneficiary":
		filters = {"applicant": docname}
	elif doctype == "IDP Family":
		# Знаходимо всіх членів сім'ї, щоб зібрати всі їхні звернення
		family_members = frappe.get_all(
			"IDP Family Member Item", filters={"parent": docname}, fields=["member"]
		)
		if not family_members:
			return {}
		member_names = [d.member for d in family_members]
		filters = {"applicant": ["in", member_names]}
	else:
		return {}

	# Отримуємо дані про звернення, групуючи їх за датою
	data = frappe.get_all(
		"IDP Appeal",
		fields=["date", "count(name) as count"],
		filters=filters,
		group_by="date",
		order_by="date",
	)

	# Форматуємо дані для теплової карти (timestamp: count)
	heatmap_data = {frappe.utils.get_timestamp(entry.date): entry.count for entry in data}

	return heatmap_data
