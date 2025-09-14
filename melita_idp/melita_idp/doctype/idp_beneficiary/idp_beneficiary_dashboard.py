from frappe import _


def get_data():
	return {
		"heatmap": True,
		"heatmap_message": _("This covers all scorecards tied to this Setup"),
		# "fieldname": "supplier",
		"method": "melita_idp.melita_idp.doctype.idp_appeal.idp_appeal.get_appeal_heatmap_data",
		# "transactions": [{"label": _("Scorecards"), "items": ["Supplier Scorecard Period"]}],
	}
