app_name = "melita_idp"
app_title = "Melita Idp"
app_publisher = "Maxim S"
app_description = "Internally displaced persons"
app_email = "maks4a@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "melita_idp",
# 		"logo": "/assets/melita_idp/logo.png",
# 		"title": "Melita Idp",
# 		"route": "/melita_idp",
# 		"has_permission": "melita_idp.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/melita_idp/css/melita_idp.css"
# app_include_js = "/assets/melita_idp/js/melita_idp.js"

# include js, css files in header of web template
# web_include_css = "/assets/melita_idp/css/melita_idp.css"
# web_include_js = "/assets/melita_idp/js/melita_idp.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "melita_idp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "melita_idp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "melita_idp.utils.jinja_methods",
# 	"filters": "melita_idp.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "melita_idp.install.before_install"
# after_install = "melita_idp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "melita_idp.uninstall.before_uninstall"
# after_uninstall = "melita_idp.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "melita_idp.utils.before_app_install"
# after_app_install = "melita_idp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "melita_idp.utils.before_app_uninstall"
# after_app_uninstall = "melita_idp.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "melita_idp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"IDP Family": "melita_idp.melita_idp.utils.permissions.get_family_permission_query_conditions",
# 	"IDP Beneficiary": "melita_idp.melita_idp.utils.permissions.get_beneficiary_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }


# Документні хуки
doc_events = {
	"IDP Beneficiary": {
		"before_rename": "melita_idp.melita_idp.utils.family_utils.handle_beneficiary_rename",
		"on_trash": "melita_idp.melita_idp.utils.family_utils.handle_beneficiary_deletion",
	},
	"IDP Family": {
		"on_update": "melita_idp.melita_idp.utils.family_utils.handle_family_update",
		"on_trash": "melita_idp.melita_idp.utils.family_utils.handle_family_deletion",
		"validate": "melita_idp.melita_idp.utils.family_utils.validate_family_structure_hook",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# 	"all": [
	# 		"melita_idp.tasks.all"
	# 	],
	"daily": ["melita_idp.melita_idp.doctype.idp_beneficiary.idp_beneficiary.update_beneficiary"],
	# 	"hourly": [
	# 		"melita_idp.tasks.hourly"
	# 	],
	"weekly": ["melita_idp.melita_idp.utils.family_utils.cleanup_empty_families"],
	# 	"monthly": [
	# 		"melita_idp.tasks.monthly"
	# 	],
}

# Testing
# -------

# before_tests = "melita_idp.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "melita_idp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "melita_idp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = ["IDP Beneficiary", "IDP Family", "IDP Appeal"]

# Request Events
# ----------------
# before_request = ["melita_idp.utils.before_request"]
# after_request = ["melita_idp.utils.after_request"]

# Job Events
# ----------
# before_job = ["melita_idp.utils.before_job"]
# after_job = ["melita_idp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"melita_idp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

default_log_clearing_doctypes = {
	"Logging DocType Name": 30  # days to retain logs
}


# Налаштування для пошуку
global_search_doctypes = {
	"IDP Beneficiary": [{"doctype": "IDP Beneficiary", "index": 1}, {"doctype": "IDP Family", "index": 2}]
}
