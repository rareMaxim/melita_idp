// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt

frappe.query_reports["Аналіз відвідувань"] = {
	filters: [
		{
			fieldname: "registration_center",
			label: __("Центр реєстрації"),
			fieldtype: "Link",
			options: "IDP Support Center",
		},
		{
			fieldname: "months_inactive",
			label: __("Період неактивності (місяці)"),
			fieldtype: "Select",
			options: "3\n6\n9\n12",
			default: "6",
		},
	],
};
