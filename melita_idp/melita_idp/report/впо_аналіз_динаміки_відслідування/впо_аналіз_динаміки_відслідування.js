// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt

frappe.query_reports["ВПО Аналіз динаміки відслідування"] = {
	filters: [
		{
			fieldname: "registration_center",
			label: __("Центр реєстрації"),
			fieldtype: "Link",
			options: "IDP Support Center",
		},
	],
};
