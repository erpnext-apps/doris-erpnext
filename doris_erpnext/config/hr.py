from frappe import _

def get_data():
	return [
		{
			"label": _("Doris Reports"),
			"icon": "icon-paper-clip",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Leave Balance",
					"doctype": "Leave Application",
				},
			]
		}
	]
