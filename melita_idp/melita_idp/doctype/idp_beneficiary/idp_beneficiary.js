// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt

frappe.ui.form.on("IDP Beneficiary", {
	refresh(frm) {
		updateBirthDayAndGenre(frm);
		add_family_ui(frm);
		// Очищуємо поле перед оновленням
		frm.fields_dict.family_info_html.html("");
		// Якщо поле "Родина" заповнене, викликаємо функцію для відображення даних
		if (frm.doc.family) {
			render_family_info(frm, frm.doc.family);
		}
	},
	family(frm) {
		// Очищуємо поле перед оновленням
		frm.fields_dict.family_info_html.html("");
		if (frm.doc.family) {
			render_family_info(frm, frm.doc.family);
		}
	},
	tax_id(frm) {
		updateBirthDayAndGenre(frm);
	},
});

// Головна функція, яка отримує дані про родину та форматує HTML
function render_family_info(frm, family_id) {
	// Робимо запит до бази даних, щоб отримати повний документ родини
	frappe.db.get_doc("IDP Family", family_id).then((family_doc) => {
		let html = `
                <div class="card">
                    <div class="card-header">
                        <strong>Родина: ${family_doc.head_of_family || ""}</strong>
                    </div>
                    <ul class="list-group list-group-flush">
            `;

		// Додаємо контактну особу
		if (family_doc.head_of_family) {
			html += `<li class="list-group-item"><strong>Контактна особа:</strong> ${family_doc.head_of_family}</li>`;
		}

		// Додаємо список членів родини, якщо він є
		if (family_doc.family_members && family_doc.family_members.length > 0) {
			html += `<li class="list-group-item"><strong>Члени родини:</strong></li>`;
			family_doc.family_members.forEach((member) => {
				// Припустимо, у вашій дочірній таблиці поле з ПІБ називається 'beneficiary'
				html += `<li class="list-group-item small" style="padding-left: 30px;">
                                <a href="/app/idp-beneficiary/${member.member}">${member.member}</a>
                             </li>`;
			});
		} else {
			html += `<li class="list-group-item">Члени родини не вказані.</li>`;
		}

		html += `
                    </ul>
                </div>
            `;

		// Вставляємо згенерований HTML у наше поле
		frm.fields_dict.family_info_html.html(html);
	});
}
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
				5
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
				5
			);
		} else if (!frm.doc.date_of_birth) {
			frm.set_value("date_of_birth", data.birthday);
			frappe.show_alert(
				{
					message: "Встановлено день народження з РНОКПП",
					indicator: "blue",
				},
				5
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
					5
				);
			return;
		} else if (!frm.doc.gender) {
			frm.set_value("gender", data.gender == "Female" ? "Жіноча" : "Чоловіча");
			frappe.show_alert(
				{
					message: "Встановлено стать з РНОКПП",
					indicator: "blue",
				},
				5
			);
		}
	});
}

let add_family_ui = function (frm) {
	// Якщо документ збережений і має прив'язану родину
	if (!frm.is_new() && frm.doc.family) {
		frm.add_custom_button(__("Додати члена родини"), () => {
			// Збираємо дані з поточної картки для автозаповнення
			const shared_data = {
				// Одразу прив'язуємо нового бенефіціара до цієї ж родини
				family: frm.doc.family,

				// Копіюємо адреси та іншу спільну інформацію
				registration_center: frm.doc.registration_center,
				origin_region: frm.doc.origin_region,
				origin_community: frm.doc.origin_community,
				current_region: frm.doc.current_region,
				current_community: frm.doc.current_community,
				current_address: frm.doc.current_address,
				registration_address: frm.doc.registration_address,
				actual_address: frm.doc.actual_address,
				// Додайте сюди інші поля, які є спільними для родини
			};

			// Створюємо новий документ з předзаповненими полями
			frappe.new_doc("IDP Beneficiary", shared_data);
		}).addClass("btn-primary");
	}
};
// Функція для додавання члена родини
function add_family_member(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Додати члена родини"),
		fields: [
			{
				label: __("Родинний зв'язок"),
				fieldname: "relationship",
				fieldtype: "Select",
				options:
					"Голова домогосподарства\nДружина/Чоловік\nСин/Донька\nБатько/Матір\nДідусь/Бабуся\nСестра/Брат\nІнше",
				reqd: 1,
			},
		],
		primary_action_label: __("Додати"),
		primary_action: (values) => {
			// Викликаємо серверний метод для додавання члена в родину
			frappe.call({
				method: "frappe.client.add_child",
				args: {
					doctype: "IDP Family",
					name: frm.doc.family,
					child_doctype: "IDP Family Table",
					values: {
						beneficiary: values.beneficiary,
						relationship: values.relationship,
					},
				},
				callback: () => {
					// Оновлюємо поле family у доданого бенефіціара
					frappe.db.set_value(
						"IDP Beneficiary",
						values.beneficiary,
						"family",
						frm.doc.family
					);
					// Перезавантажуємо форму, щоб побачити зміни
					frm.reload_doc();
				},
			});
			dialog.hide();
		},
	});
	dialog.show();
}
