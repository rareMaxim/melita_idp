# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class IDPFamily(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from melita_idp.melita_idp.doctype.idp_family_member_item.idp_family_member_item import (
			IDPFamilyMemberItem,
		)

		family_members: DF.Table[IDPFamilyMemberItem]
		head_of_family: DF.Link | None
		in_difficult_life_circumstances: DF.Check
		lives_in_mkp: DF.Check
	# end: auto-generated types

	pass
