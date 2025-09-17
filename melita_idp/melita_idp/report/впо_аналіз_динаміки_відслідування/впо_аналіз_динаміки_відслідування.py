# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_months, date_diff, today


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)

	# Дані для діаграми
	chart = get_chart_data(data)

	# Дані для зведеної інформації
	report_summary = get_report_summary(data)

	return columns, data, None, chart, report_summary


def get_columns():
	return [
		{
			"label": _("Бенефіціар"),
			"fieldname": "beneficiary",
			"fieldtype": "Link",
			"options": "IDP Beneficiary",
			"width": 200,
		},
		{
			"label": _("Дата останнього візиту"),
			"fieldname": "last_visit_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": _("Днів з останнього візиту"),
			"fieldname": "days_since_visit",
			"fieldtype": "Int",
			"width": 100,
		},
		{"label": _("Телефон"), "fieldname": "phone", "fieldtype": "Data", "width": 150},
		{
			"label": _("Сім'я"),
			"fieldname": "idp_family",
			"fieldtype": "Link",
			"options": "IDP Family",
			"width": 200,
		},
		{
			"label": _("Центр реєстрації"),
			"fieldname": "registration_center",
			"fieldtype": "Link",
			"options": "IDP Support Center",
			"width": 180,
		},
	]


def get_data(filters):
	months = filters.get("months_inactive") or 6
	try:
		months = int(months)
	except (ValueError, TypeError):
		months = 6

	inactive_since_date = add_months(today(), -months)

	conditions = "AND b.status = 'Активний'"
	if filters.get("registration_center"):
		conditions += " AND b.registration_center = %(registration_center)s"

	sql_query = f"""
        SELECT
            b.name as beneficiary,
            b.last_visit_date,
            b.phone,
            b.idp_family,
            b.registration_center
        FROM
            `tabIDP Beneficiary` as b
        WHERE
            (b.last_visit_date IS NULL OR b.last_visit_date < %(inactive_since_date)s)
            {conditions}
    """

	params = {
		"inactive_since_date": inactive_since_date,
		"registration_center": filters.get("registration_center"),
	}

	beneficiaries = frappe.db.sql(sql_query, params, as_dict=1)

	for row in beneficiaries:
		if row.last_visit_date:
			row.days_since_visit = date_diff(today(), row.last_visit_date)
		else:
			registration_date = frappe.db.get_value("IDP Beneficiary", row.beneficiary, "registration_date")
			row.days_since_visit = date_diff(today(), registration_date) if registration_date else None

	return beneficiaries


def get_chart_data(data):
	"""Готує дані для діаграми."""
	center_counts = {}
	for row in data:
		center = row.get("registration_center") or "Не вказано"
		center_counts[center] = center_counts.get(center, 0) + 1

	labels = list(center_counts.keys())
	values = list(center_counts.values())

	return {
		"data": {"labels": labels, "datasets": [{"name": "Кількість бенефіціарів", "values": values}]},
		"type": "bar",
		"height": 280,
	}


def get_report_summary(data):
	"""Готує зведену інформацію."""
	total_inactive = len(data)
	return [
		{
			"value": total_inactive,
			"label": "Загальна кількість неактивних бенефіціарів",
			"datatype": "Int",
			"indicator": "Red" if total_inactive > 0 else "Green",
		}
	]
