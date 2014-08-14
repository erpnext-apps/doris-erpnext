# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe
from frappe import _, throw
from frappe.utils import getdate, formatdate, now_datetime, flt
from frappe.defaults import get_user_permissions
from erpnext.hr.doctype.leave_application.leave_application import get_events as get_leave_application_events, add_leaves

class LeaveApplicationPeriodError(frappe.ValidationError): pass

# called via hooks.py
def validate_leave_application(doc, method):
	year_start_date, year_end_date = get_fiscal_year_dates(doc.fiscal_year)
	from_date = getdate(doc.from_date)
	to_date = getdate(doc.to_date)

	if not (year_start_date <= from_date <= to_date <= year_end_date):
		throw(_("From Date and To Date should be within the selected Fiscal Year's period: {0} to {1}").format(
			formatdate(year_start_date), formatdate(year_end_date)), LeaveApplicationPeriodError)

# In javascript, "method": "doris_erpnext.doris_erpnext_extensions.leave_application.get_leave_balance_to_date"
@frappe.whitelist()
def get_leave_balance_to_date(employee, leave_type, fiscal_year):
	year_start_date, year_end_date = get_fiscal_year_dates(fiscal_year)

	# get today's date as per timezone in System Settings
	today = now_datetime().date()

	out = {"leave_balance_to_date": 0.0}

	if year_start_date <= today <= year_end_date:
		employee = frappe.get_doc("Employee", employee)

		annual_leave_entitlement = flt(employee.annual_leave_entitlement)
		if leave_type != "Annual Leave":
			annual_leave_entitlement = 0.0

		start_date = getdate(employee.date_of_joining)
		if start_date <= year_start_date:
			start_date = year_start_date

		number_of_days = (today - start_date).days
		carry_forwarded_leaves = flt(frappe.db.get_value("Leave Allocation",
			{"employee": employee, "leave_type": leave_type, "fiscal_year": fiscal_year, "docstatus": 1},
			"carry_forwarded_leaves"))

		leaves_allocated = ((number_of_days * annual_leave_entitlement) / 365.0) + carry_forwarded_leaves

		leaves_applied = frappe.db.sql("""select sum(total_leave_days)
			from `tabLeave Application`
			where employee=%s and leave_type=%s and fiscal_year=%s
				and status='Approved' and docstatus=1""",
			(employee, leave_type, fiscal_year))
		leaves_applied = flt(leaves_applied[0][0]) if leaves_applied else 0.0

		out["leave_balance_to_date"] = leaves_allocated - leaves_applied

	return out

def get_fiscal_year_dates(fiscal_year):
	year_start_date, year_end_date = frappe.db.get_value("Fiscal Year", fiscal_year,
		["year_start_date", "year_end_date"])

	year_start_date = getdate(year_start_date)
	year_end_date = getdate(year_end_date)

	return year_start_date, year_end_date

@frappe.whitelist()
def get_events(start, end):
	# get results from standard method
	events = get_leave_application_events(start, end)

	add_additional_department_leaves(events, start, end)

	return events

def add_additional_department_leaves(events, start, end):
	user = frappe.session.user

	employee = frappe.db.get_value("Employee", {"user_id": user}, ["department", "company"], as_dict=True)
	if not employee:
		return

	departments = get_user_permissions().get("Department", [])
	if employee.department and employee.department in (departments or []):
		# since leaves for this department are already added by the standard method
		departments.remove(employee.department)

	if not departments:
		return

	department_employees = frappe.db.sql_list("""select name from `tabEmployee`
		where company=%s and department in ({0})""".format(", ".join(["%s"] * len(departments))),
		tuple([employee.company] + departments))

	# leaves for additional department employees
	match_conditions = "employee in (\"{0}\")".format('", "'.join(department_employees))
	add_leaves(events, start, end, match_conditions=match_conditions)
