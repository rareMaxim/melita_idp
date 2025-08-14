// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt
function updateBirthDayAndGenre(frm) {

    if (!frm.doc.tax_id || (frm.doc.tax_id.length != 10)) { return };
    frappe.require('/assets/melita_idp/js/taxCode_utils.js', () => {
        function formatDate(date) {
            return frappe.format(date, { fieldtype: 'Date' });;
        }
        var data = taxCodeInfo(frm.doc.tax_id);
        // console.log(data);
        if (data.error == "ErrInvalidControlDigit") {
            frappe.show_alert({
                message: "Невірно введенний РНОКПП",
                indicator: 'orange'
            }, 5);
            return;
        };
        if (frm.doc.date_of_birth && (formatDate(frm.doc.date_of_birth) != formatDate(data.birthday))) {
            frappe.show_alert({
                message: "Дата народження не відповідає РНОКПП",
                indicator: 'orange'
            }, 5);
        } else if (!frm.doc.date_of_birth) {
            frm.set_value('date_of_birth', data.birthday);
            frappe.show_alert({
                message: "Встановлено день народження з РНОКПП",
                indicator: 'blue'
            }, 5);
        };
        if (frm.doc.gender) {
            let sex = data.gender == "Female" ? "Жіноча" : "Чоловіча";
            if (frm.doc.gender != sex)
                frappe.show_alert({
                    message: 'Стать не відповідає РНОКПП',
                    indicator: 'orange'
                }, 5);
            return
        } else if (!frm.doc.gender) {
            frm.set_value('gender', data.gender == "Female" ? "Жіноча" : "Чоловіча");
            frappe.show_alert({
                message: "Встановлено стать з РНОКПП",
                indicator: 'blue'
            }, 5);
        };
    })
};
frappe.ui.form.on("IDP Beneficiary", {
    refresh(frm) {
        updateBirthDayAndGenre(frm);
    },
    tax_id(frm) {
        updateBirthDayAndGenre(frm);
    },
});
