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

		member: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		relationship: DF.Literal[
			"\u0413\u043e\u043b\u043e\u0432\u0430",
			"\u0414\u0440\u0443\u0436\u0438\u043d\u0430/\u0427\u043e\u043b\u043e\u0432\u0456\u043a",
			"\u0414\u0438\u0442\u0438\u043d\u0430",
			"\u0411\u0430\u0442\u044c\u043a\u043e/\u041c\u0430\u0442\u0438",
			"\u0414\u0456\u0434\u0443\u0441\u044c/\u0411\u0430\u0431\u0443\u0441\u044f",
			"\u0406\u043d\u0448\u0435",
		]
	# end: auto-generated types

	pass
