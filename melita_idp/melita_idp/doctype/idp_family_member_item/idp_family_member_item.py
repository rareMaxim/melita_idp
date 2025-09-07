# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class IDPFamilyMemberItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		age: DF.Int
		gender: DF.Data | None
		member: DF.Link
		member_name: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		phone: DF.Data | None
		relationship: DF.Literal[
			"\u0413\u043e\u043b\u043e\u0432\u0430",
			"\u0427\u043e\u043b\u043e\u0432\u0456\u043a/\u0414\u0440\u0443\u0436\u0438\u043d\u0430",
			"\u0421\u0438\u043d/\u0414\u043e\u043d\u044c\u043a\u0430",
			"\u0411\u0430\u0442\u044c\u043a\u043e/\u041c\u0430\u0442\u0438",
			"\u0411\u0440\u0430\u0442/\u0421\u0435\u0441\u0442\u0440\u0430",
			"\u0414\u0456\u0434\u0443\u0441\u044c/\u0411\u0430\u0431\u0443\u0441\u044f",
			"\u041e\u043d\u0443\u043a/\u041e\u043d\u0443\u0447\u043a\u0430",
			"\u0406\u043d\u0448\u0438\u0439 \u0440\u043e\u0434\u0438\u0447",
			"\u041e\u043f\u0456\u043a\u0443\u0432\u0430\u043d\u0438\u0439",
		]
	# end: auto-generated types

	pass
