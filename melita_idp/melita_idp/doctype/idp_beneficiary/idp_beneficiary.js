// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt

frappe.ui.form.on("IDP Beneficiary", {
	refresh(frm) {
		frm.dashboard.add_indicator("Total Sales", "green");
		updateBirthDayAndGenre(frm);
		set_document_type(frm);
		addFamilyButtons(frm);
		render_family_members(frm);
	},
	document(frm) {
		set_document_type(frm);
	},
	tax_id(frm) {
		updateBirthDayAndGenre(frm);
	},
	onload(frm) {
		// Якщо це новий документ з переданими параметрами, заповнюємо дані
		if (frm.is_new() && frappe.route_options) {
			fillFamilyMemberData(frm);
		}
	},
	idp_family(frm) {
		render_family_members(frm);
	},
	after_save(frm) {
		// Якщо це новий член сім'ї з тимчасовою роллю, додаємо його до сім'ї
		if (frm.doc.temp_relationship && frm.doc.idp_family) {
			frappe.call({
				method: "melita_idp.melita_idp.doctype.idp_family.idp_family.add_member_to_family",
				args: {
					family_id: frm.doc.idp_family,
					member_id: frm.doc.name,
					relationship: frm.doc.temp_relationship,
				},
				callback: function (r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __("Додано до сім'ї як {0}", [
								frm.doc.temp_relationship,
							]),
							indicator: "green",
						});
						// Очищуємо тимчасове поле, щоб це не виконувалось знову
						frappe.db.set_value(
							"IDP Beneficiary",
							frm.doc.name,
							"temp_relationship",
							null,
						);
						frm.doc.temp_relationship = null; // Очищуємо також в локальному об'єкті
					} else {
						frappe.show_alert({
							message: __("Не вдалося додати до сім'ї: {0}", [
								r.message.message,
							]),
							indicator: "red",
						});
					}
				},
			});
		}
	},
});

function updateBirthDayAndGenre(frm) {
	if (!frm.doc.tax_id || frm.doc.tax_id.length != 10) {
		return;
	}
	frappe.require("/assets/melita_idp/js/taxCode_utils.js", () => {
		function formatDate(date) {
			return frappe.format(date, { fieldtype: "Date" });
		}
		// eslint-disable-next-line no-undef
		var data = taxCodeInfo(frm.doc.tax_id);
		if (data.error == "ErrInvalidControlDigit") {
			frappe.show_alert(
				{ message: "Невірно введенний РНОКПП", indicator: "orange" },
				5,
			);
			return;
		}
		if (
			frm.doc.date_of_birth &&
			formatDate(frm.doc.date_of_birth) != formatDate(data.birthday)
		) {
			frappe.show_alert(
				{
					message: "Дата народження не відповідає РНОКПП",
					indicator: "orange",
				},
				5,
			);
		} else if (!frm.doc.date_of_birth) {
			frm.set_value("date_of_birth", data.birthday);
			frappe.show_alert(
				{
					message: "Встановлено день народження з РНОКПП",
					indicator: "blue",
				},
				5,
			);
		}
		if (frm.doc.gender) {
			let sex = data.gender == "Female" ? "Жіноча" : "Чоловіча";
			if (frm.doc.gender != sex)
				frappe.show_alert(
					{
						message: "Стать не відповідає РНОКПП",
						indicator: "orange",
					},
					5,
				);
		} else if (!frm.doc.gender) {
			frm.set_value(
				"gender",
				data.gender == "Female" ? "Жіноча" : "Чоловіча",
			);
			frappe.show_alert(
				{ message: "Встановлено стать з РНОКПП", indicator: "blue" },
				5,
			);
		}
	});
}

function addFamilyButtons(frm) {
	frm.page.clear_secondary_action();
	if (!frm.doc.__islocal && frm.doc.idp_family) {
		frm.add_custom_button(
			__("Додати члена сім'ї"),
			() => addNewFamilyMember(frm),
			__("Сім'я"),
		);
		frm.add_custom_button(
			__("Переглянути сім'ю"),
			() => frappe.set_route("Form", "IDP Family", frm.doc.idp_family),
			__("Сім'я"),
		);
		frm.add_custom_button(
			__("Перенести в іншу сім'ю"),
			() => open_transfer_dialog(frm),
			__("Сім'я"),
		);

		frappe.call({
			method: "melita_idp.melita_idp.doctype.idp_family.idp_family.get_family_head",
			args: { family_id: frm.doc.idp_family },
			callback: function (r) {
				if (r.message && r.message !== frm.doc.name) {
					frm.add_custom_button(
						__("Перейти до голови сім'ї"),
						() =>
							frappe.set_route(
								"Form",
								"IDP Beneficiary",
								r.message,
							),
						__("Сім'я"),
					);
				}
			},
		});
	}
}

function open_transfer_dialog(frm) {
	let d = new frappe.ui.Dialog({
		title: __("Перенести в іншу сім'ю"),
		fields: [
			{
				label: __("Перенести до сім'ї, де є"),
				fieldname: "target_beneficiary",
				fieldtype: "Link",
				options: "IDP Beneficiary",
				reqd: 1,
				description: __("Вкажіть ПІБ, номер телефону або РНОКПП"),
			},
			{
				label: "Роль в новій сім'ї",
				fieldname: "relationship",
				fieldtype: "Select",
				options:
					"\nЧоловік/Дружина\nСин/Донька\nБатько/Мати\nБрат/Сестра\nДідусь/Бабуся\nОнук/Онучка\nІнший родич\nОпікуваний",
				reqd: 1,
				default: "Інший родич",
			},
		],
		primary_action_label: __("Перенести"),
		primary_action(values) {
			frappe.call({
				method: "melita_idp.melita_idp.doctype.idp_beneficiary.idp_beneficiary.transfer_beneficiary_to_another_beneficiarys_family",
				args: {
					current_beneficiary_id: frm.doc.name,
					target_beneficiary_id: values.target_beneficiary,
					relationship: values.relationship,
				},
				callback: function (r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: __("Бенефіціара перенесено"),
							indicator: "green",
						});
						frm.reload_doc();
					} else {
						frappe.show_alert({
							message: __("Помилка перенесення: {0}", [
								r.message.message || r.exc,
							]),
							indicator: "red",
						});
					}
				},
			});
			d.hide();
		},
	});
	d.show();
}

function addNewFamilyMember(frm) {
	let d = new frappe.ui.Dialog({
		title: __("Виберіть роль в сім'ї"),
		fields: [
			{
				label: "Роль в сім'ї",
				fieldname: "relationship",
				fieldtype: "Select",
				options:
					"\nЧоловік/Дружина\nСин/Донька\nБатько/Мати\nБрат/Сестра\nДідусь/Бабуся\nОнук/Онучка\nІнший родич\nОпікуваний",
				reqd: 1,
				default: "Інший родич",
			},
		],
		primary_action_label: __("Створити"),
		primary_action(values) {
			d.hide();
			frappe.call({
				method: "melita_idp.melita_idp.doctype.idp_beneficiary.idp_beneficiary.get_family_common_fields",
				args: {
					family_id: frm.doc.idp_family,
				},
				callback: function (r) {
					if (r.message) {
						r.message.idp_family = frm.doc.idp_family;
						r.message.temp_relationship = values.relationship; // Використовуємо обрану роль
						frappe.route_options = r.message;
						frappe.new_doc("IDP Beneficiary");
					}
				},
			});
		},
	});
	d.show();
}

function fillFamilyMemberData(frm) {
	if (frappe.route_options) {
		Object.keys(frappe.route_options).forEach(function (key) {
			if (frappe.route_options[key] && frm.fields_dict[key]) {
				frm.set_value(key, frappe.route_options[key]);
			}
		});
		frappe.show_alert(
			{
				message: "Заповнено спільні поля для члена сім'ї",
				indicator: "blue",
			},
			3,
		);
		frappe.route_options = null;
	}
}

function render_family_members(frm) {
	if (!frm.fields_dict["family_members_html"] || !frm.doc.idp_family) {
		if (frm.fields_dict["family_members_html"]) {
			$(frm.fields_dict["family_members_html"].wrapper).html(
				"<p>Сім'я не вказана.</p>",
			);
		}
		return;
	}
	$(frm.fields_dict["family_members_html"].wrapper).html(
		"<p>Завантаження даних сім'ї...</p>",
	);
	frappe.call({
		method: "melita_idp.melita_idp.doctype.idp_beneficiary.idp_beneficiary.get_family_members_data",
		args: { family_id: frm.doc.idp_family },
		callback: function (r) {
			let family_members = r.message;
			let html_content = "";
			if (family_members && family_members.length > 0) {
				html_content = "<div class='family-members-list'>";
				family_members.forEach(function (member, i) {
					html_content += `
                        <div class='family-member-card' style='border: 1px solid #eee; padding: 10px; margin-bottom: 10px; border-radius: 5px;'>
                            <h4>${i + 1}. <a href='/app/idp-beneficiary/${member.name}'>${member.full_name || member.name}</a> (${member.relationship})</h4>
                            <p><strong>Телефон:</strong> ${member.phone || "Не вказано"}</p>
                            <p><strong>Вік:</strong> ${member.age || "Не вказано"}</p>
                            <p><strong>Стать:</strong> ${member.gender || "Не вказано"}</p>
                        </div>
                    `;
				});
				html_content += "</div>";
			} else {
				html_content =
					"<p>У цій сім'ї немає зареєстрованих членів.</p>";
			}
			const field_wrapper = $(
				frm.fields_dict["family_members_html"].wrapper,
			);
			field_wrapper.html(html_content);
		},
		error: function () {
			const field_wrapper = $(
				frm.fields_dict["family_members_html"].wrapper,
			);
			field_wrapper.html(
				"<p style='color: red;'>Не вдалося завантажити дані про сім'ю.</p>",
			);
		},
	});
}

function set_document_type(frm) {
	let doc_number = frm.doc.document;
	if (!doc_number) {
		if (frm.doc.document_type) {
			frm.set_value("document_type", "");
			frappe.show_alert(
				{ message: __("Тип документа скинуто."), indicator: "orange" },
				2,
			);
		}
		return;
	}
	doc_number = doc_number.toUpperCase().trim();
	let doc_type = "";
	if (/^\d{8}-\d{5}$/.test(doc_number) || /^\d{9}$/.test(doc_number)) {
		doc_type = "ID-картка";
	} else if (/^[А-ЩЬЮЯҐЄІЇ]{2}\s?\d{6}$/.test(doc_number)) {
		doc_type = "Паспорт";
	} else if (/^[IІА-ЩЬЮЯҐЄІЇ]-[А-ЩЬЮЯҐЄІЇ]{2}\s?\d{6}$/.test(doc_number)) {
		doc_type = "Свідоцтво про народження";
	}
	if (doc_type && frm.doc.document_type !== doc_type) {
		frm.set_value("document_type", doc_type);
		frappe.show_alert(
			{
				message: __("Встановлено тип документа: {0}", [doc_type]),
				indicator: "green",
			},
			2,
		);
	} else if (!doc_type && frm.doc.document_type) {
		frm.set_value("document_type", "");
		frappe.show_alert(
			{
				message: __("Тип документа скинуто (не розпізнано)."),
				indicator: "orange",
			},
			2,
		);
	}
}
