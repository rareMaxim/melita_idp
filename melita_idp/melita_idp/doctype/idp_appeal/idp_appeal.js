// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt

frappe.ui.form.on("IDP Appeal", {
	refresh(frm) {},
	service_category(frm) {
		frm.set_query("service_name", function () {
			return {
				filters: {
					category: frm.doc.service_category,
					enabled: 1,
				},
			};
		});
	},
});
