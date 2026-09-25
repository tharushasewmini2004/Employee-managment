# run_day2.py
from employee import Employee
from employee_repository import EmployeeRepository

def demo_employee_class():
   print("=== Assignment C: Employee class ===")
   emp = Employee(1, "John", "john@company.com", 100000, "IT")
   print("Details:", emp.get_details())
   print("Annual salary:", emp.calculate_annual_salary())
   emp.update_salary(110000)
   print("After raise:", emp.salary)
   try:
       emp.update_salary(-5000)
   except ValueError as error:
       print("Blocked:", error)
   print("Salary is still:", emp.salary)
   try:
       Employee(2, "Bad", "bad@company.com", -1, "IT")
   except ValueError as error:
       print("Blocked:", error)

def demo_repository():
   print("\n=== Assignment D: EmployeeRepository ===")
   repo = EmployeeRepository()
   repo.create(Employee(1, "John", "john@company.com", 100000, "IT"))
   repo.create(Employee(2, "Jane", "jane@company.com", 120000, "HR"))
   repo.create(Employee(3, "Mike", "mike@company.com", 90000, "Finance"))
   print("All:", repo.get_all())
   print("Get id 2:", repo.get_by_id(2))
   print("Get id 99:", repo.get_by_id(99))
   repo.update(3, salary=95000, status="inactive")
   print("After update:", repo.get_by_id(3).get_details())
   print("Delete id 1:", repo.delete(1))
   print("Delete id 1 again:", repo.delete(1))
   print("Remaining:", repo.get_all())
   try:
       repo.create(Employee(2, "Copy", "copy@company.com", 50000, "IT"))
   except ValueError as error:
       print("Blocked:", error)

if __name__ == "__main__":
   demo_employee_class()
   demo_repository()
   