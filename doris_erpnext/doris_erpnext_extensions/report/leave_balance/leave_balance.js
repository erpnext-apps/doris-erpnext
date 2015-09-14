// Copyright (c) 2013, Doris and contributors
// For license information, please see license.txt

frappe.query_reports["Leave Balance"] = {
	"filters": [
		{
			"fieldname":"fiscal_year",
			"label": "Fiscal Year",
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year")
		},
		{
			"fieldname":"company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("company")
		},
		    {
			"fieldname":"status",
			"label": "Status",
			"fieldtype": "Select",
	        "options": ["","Active","Left"],
			"default": "Active"
		}
	]
}
