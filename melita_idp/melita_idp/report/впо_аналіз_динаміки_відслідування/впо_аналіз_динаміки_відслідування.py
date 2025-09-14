# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe import _
from frappe.utils.data import add_months, date_diff, today


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	data = get_data(filters)

	return columns, data


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
	six_months_ago = add_months(today(), -6)

	conditions = "AND b.status = 'Активний'"
	if filters and filters.get("registration_center"):
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
            (b.last_visit_date IS NULL OR b.last_visit_date < %(six_months_ago)s)
            {conditions}
    """

	beneficiaries = frappe.db.sql(
		sql_query,
		{
			"six_months_ago": six_months_ago,
			"registration_center": filters.get("registration_center") if filters else None,
		},
		as_dict=1,
	)

	for row in beneficiaries:
		if row.last_visit_date:
			row.days_since_visit = date_diff(today(), row.last_visit_date)
		else:
			# Якщо візитів не було, рахуємо з дати реєстрації
			registration_date = frappe.db.get_value("IDP Beneficiary", row.beneficiary, "registration_date")
			if registration_date:
				row.days_since_visit = date_diff(today(), registration_date)
			else:
				row.days_since_visit = "N/A"

	return beneficiaries
