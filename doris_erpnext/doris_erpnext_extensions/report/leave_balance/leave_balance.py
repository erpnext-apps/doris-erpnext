# Copyright (c) 2013, Doris and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	if not filters: filters = {}

	employee_filters =[]

	if filters.get("company"):
		employee_filters.append(["Employee", "company", "=", filters.get("company")])

	if filters.get("status"):
		employee_filters.append(["Employee", "status", "=", filters.get("status")])


	employees = frappe.get_list(doctype="Employee", fields=["name", "employee_name","company", "department", "status", "employment_type"],
		filters=employee_filters)
	leave_types = frappe.db.sql_list("select name from `tabLeave Type`")

	if filters.get("fiscal_year"):
		fiscal_years = [filters["fiscal_year"]]
	else:
		fiscal_years = frappe.db.sql_list("select name from `tabFiscal Year` order by name desc")

	employee_in = '", "'.join([e.name for e in employees])

	allocations = frappe.db.sql("""select employee, fiscal_year, leave_type, carry_forwarded_leaves, new_leaves_allocated, total_leaves_allocated
	 	from `tabLeave Allocation`
		where docstatus=1 and employee in ("%s")""" % employee_in, as_dict=True)

	takens_leaves = frappe.db.sql("""select employee, fiscal_year, leave_type, SUM(total_leave_days) as leaves
			from `tabLeave Application`
			where status="Approved" and docstatus = 1 and from_date <=CURDATE() and employee in ("%s")
			group by employee, fiscal_year, leave_type""" % employee_in, as_dict=True)

	upcoming_leaves = frappe.db.sql("""select employee, fiscal_year, leave_type, SUM(total_leave_days) as leaves
			from `tabLeave Application`
			where status="Approved" and docstatus = 1 and from_date > CURDATE() and employee in ("%s")
			group by employee, fiscal_year, leave_type""" % employee_in, as_dict=True)

	columns = [
		"Fiscal Year", "Employee:Link/Employee:150", "Employee Name::200", "Company::150", "Department::150","Status"
	]

	for leave_type in leave_types:
		if leave_type == "Annual Leave":
			columns.append(leave_type + " - Carry Forwarded Leaves:Float")
			columns.append(leave_type + " - Entitlement:Float")
			columns.append(leave_type + " - Total Allocated:Float")
			columns.append(leave_type + " - Already Taken:Float")
			columns.append(leave_type + " - Upcoming:Float")
			columns.append(leave_type + " - Total Taken:Float")
			columns.append(leave_type + " - Remaining Balance:Float")
		else:

			columns.append(leave_type + " -  Total Taken:Float")

	data = {}
	for d in allocations:
		data.setdefault((d.fiscal_year, d.employee,
			d.leave_type), frappe._dict()).carry_forwarded_leaves = d.carry_forwarded_leaves

		data.setdefault((d.fiscal_year, d.employee,
			d.leave_type), frappe._dict()).entitlement = d.new_leaves_allocated

		data.setdefault((d.fiscal_year, d.employee,
			d.leave_type), frappe._dict()).total_leaves_allocation = d.total_leaves_allocated

	for d in takens_leaves:
		data.setdefault((d.fiscal_year, d.employee,
			d.leave_type), frappe._dict()).leaves_taken = d.leaves

	for d in upcoming_leaves:
		data.setdefault((d.fiscal_year, d.employee,
			d.leave_type), frappe._dict()).leaves_upcoming = d.leaves


	result = []
	for fiscal_year in fiscal_years:
		for employee in employees:
			if employee.employment_type != "Contractor":
				row = [fiscal_year, employee.name, employee.employee_name, employee.company, employee.department, employee.status]
				result.append(row)
				for leave_type in leave_types:
					tmp = data.get((fiscal_year, employee.name, leave_type), frappe._dict())
					total_leave_taken = (tmp.leaves_taken or 0) + (tmp.leaves_upcoming or 0)

					if leave_type == "Annual Leave":
						row.append(tmp.carry_forwarded_leaves or "")
						row.append(tmp.entitlement or "")
						row.append(tmp.total_leaves_allocation or "")
						row.append(tmp.leaves_taken or 0)
						row.append(tmp.leaves_upcoming or 0)
						row.append(total_leave_taken)
						row.append((tmp.total_leaves_allocation or 0) - total_leave_taken)
					else:
						if total_leave_taken != 0:
							row.append(total_leave_taken)
						else:
							row.append("")
	return columns, result
