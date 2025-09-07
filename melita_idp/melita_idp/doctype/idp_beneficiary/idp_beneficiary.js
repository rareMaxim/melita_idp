// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt

frappe.ui.form.on("IDP Beneficiary", {
	refresh(frm) {
		updateBirthDayAndGenre(frm);
		addFamilyButtons(frm);
		render_family_members(frm);
		// frm.dirty(false); // Скидаємо "брудний" стан форми після оновлення відображення сім'ї
	},
	tax_id(frm) {
		updateBirthDayAndGenre(frm);
	},
	onload(frm) {
		// Якщо це новий документ з переданими параметрами для члена сім'ї
		if (frm.is_new() && frappe.route_options) {
			fillFamilyMemberData(frm);
		}
	},
	idp_family(frm) {
		render_family_members(frm);
	},
	after_save(frm) {
		// Якщо це новий член сім'ї, додаємо його до сім'ї
		if (frm.doc.temp_relationship && frm.doc.idp_family) {
			addMemberToFamily(frm);
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
		// console.log(data);
		if (data.error == "ErrInvalidControlDigit") {
			frappe.show_alert(
				{
					message: "Невірно введенний РНОКПП",
					indicator: "orange",
				},
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
			return;
		} else if (!frm.doc.gender) {
			frm.set_value(
				"gender",
				data.gender == "Female" ? "Жіноча" : "Чоловіча",
			);
			frappe.show_alert(
				{
					message: "Встановлено стать з РНОКПП",
					indicator: "blue",
				},
				5,
			);
		}
	});
}

function addFamilyButtons(frm) {
	// Видаляємо старі кнопки якщо вони є
	frm.page.clear_secondary_action();

	if (!frm.doc.__islocal && frm.doc.idp_family) {
		// Кнопка для додавання нового члена сім'ї
		frm.add_custom_button(
			__("Додати члена сім'ї"),
			function () {
				addNewFamilyMember(frm);
			},
			__("Сім'я"),
		);

		// Кнопка для переходу до сім'ї
		frm.add_custom_button(
			__("Переглянути сім'ю"),
			function () {
				frappe.set_route("Form", "IDP Family", frm.doc.idp_family);
			},
			__("Сім'я"),
		);

		// Перевіряємо, чи це голова сім'ї
		frappe.call({
			method: "melita_idp.melita_idp.doctype.idp_family.idp_family.get_family_head",
			args: {
				family_id: frm.doc.idp_family,
			},
			callback: function (r) {
				if (r.message && r.message !== frm.doc.name) {
					// Якщо це не голова сім'ї, додаємо кнопку переходу до голови
					frm.add_custom_button(
						__("Перейти до голови сім'ї"),
						function () {
							frappe.set_route(
								"Form",
								"IDP Beneficiary",
								r.message,
							);
						},
						__("Сім'я"),
					);
				}
			},
		});
	}
}

function addNewFamilyMember(frm) {
	frappe.call({
		method: "melita_idp.melita_idp.doctype.idp_beneficiary.idp_beneficiary.get_family_common_fields",
		args: {
			family_id: frm.doc.idp_family,
		},
		callback: function (r) {
			if (r.message) {
				// Додаємо ідентифікатор сім'ї до спільних даних
				r.message.idp_family = frm.doc.idp_family;
				r.message.temp_relationship = "Член сім'ї";

				// Зберігаємо дані в route_options для передачі в нову форму
				frappe.route_options = r.message;

				// Переходимо до нової форми створення бенефіціара
				frappe.new_doc("IDP Beneficiary");
			}
		},
	});
}

function fillFamilyMemberData(frm) {
	// Заповнюємо поля новими даними з route_options
	if (frappe.route_options) {
		Object.keys(frappe.route_options).forEach(function (key) {
			if (frappe.route_options[key] && frm.fields_dict[key]) {
				frm.set_value(key, frappe.route_options[key]);
			}
		});

		// Показуємо повідомлення
		frappe.show_alert(
			{
				message: "Заповнено спільні поля для члена сім'ї",
				indicator: "blue",
			},
			3,
		);

		// Очищаємо route_options
		frappe.route_options = null;
	}
}

function addMemberToFamily(frm) {
	let family_doc = frappe.get_doc("IDP Family", frm.doc.idp_family);
	// Перевіряємо, чи не є вже цей бенефіціар членом сім'ї
	let already_member = family_doc.family_members.some(function (member) {
		return member.member === frm.doc.name;
	});

	if (!already_member) {
		// Показуємо діалог вибору ролі в сім'ї
		showRelationshipDialog(frm, family_doc);
	} else {
		// Очищаємо тимчасове поле
		frm.set_value("temp_relationship", "");
	}
}

function showRelationshipDialog(frm, family_doc) {
	let d = new frappe.ui.Dialog({
		title: "Виберіть роль в сім'ї",
		fields: [
			{
				label: "Роль в сім'ї",
				fieldname: "relationship",
				fieldtype: "Select",
				options: [
					"Чоловік/Дружина",
					"Син/Донька",
					"Батько/Мати",
					"Брат/Сестра",
					"Дідусь/Бабуся",
					"Онук/Онучка",
					"Інший родич",
					"Опікуваний",
				].join("\n"),
				reqd: 1,
				default: "Член сім'ї",
			},
		],
		primary_action_label: "Додати до сім'ї",
		primary_action(values) {
			// Додаємо нового члена до сім'ї
			family_doc.family_members.push({
				member: frm.doc.name,
				relationship: values.relationship,
			});

			// Зберігаємо оновлену сім'ю
			frappe.call({
				method: "frappe.client.save",
				args: {
					doc: family_doc,
				},
				callback: function (r) {
					if (r.message) {
						frappe.show_alert(
							{
								message:
									"Додано до сім'ї як " + values.relationship,
								indicator: "green",
							},
							3,
						);

						// Очищаємо тимчасове поле
						frm.set_value("temp_relationship", "");
						frm.save();

						// Оновлюємо відображення
						render_family_members(frm);
					}
				},
			});

			d.hide();
		},
	});

	d.show();
}

function render_family_members(frm) {
	// Перевіряємо, чи є поле `family_members_html` та ID сім'ї
	if (!frm.fields_dict["family_members_html"] || !frm.doc.idp_family) {
		// Якщо немає, очищуємо поле і виходимо
		if (frm.fields_dict["family_members_html"]) {
			$(frm.fields_dict["family_members_html"].wrapper).html(
				"<p>Сім'я не вказана.</p>",
			);
		}
		return;
	}

	// Показуємо індикатор завантаження
	$(frm.fields_dict["family_members_html"].wrapper).html(
		"<p>Завантаження даних сім'ї...</p>",
	);

	// Викликаємо наш новий серверний метод
	frappe.call({
		method: "melita_idp.melita_idp.doctype.idp_beneficiary.idp_beneficiary.get_family_members_data",
		args: {
			family_id: frm.doc.idp_family,
		},
		callback: function (r) {
			let family_members = r.message;
			let html_content = "";

			if (family_members && family_members.length > 0) {
				html_content = "<div class='family-members-list'>";
				family_members.forEach(function (member, i) {
					// Генеруємо HTML-картку для кожного члена сім'ї
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

			// !!! Ключовий момент: оновлюємо HTML напряму, не через set_value !!!
			const field_wrapper = $(
				frm.fields_dict["family_members_html"].wrapper,
			);
			field_wrapper.html(html_content);
		},
		error: function (r) {
			// Обробка помилок
			const field_wrapper = $(
				frm.fields_dict["family_members_html"].wrapper,
			);
			field_wrapper.html(
				"<p style='color: red;'>Не вдалося завантажити дані про сім'ю.</p>",
			);
		},
	});
}
