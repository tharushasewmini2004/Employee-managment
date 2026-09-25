# employee_repository.py

class EmployeeRepository:
   """Stores Employee objects in memory. Replaced by a real database on Day 4."""
   ALLOWED_FIELDS = {"name", "email", "salary", "department", "status"}
   def __init__(self):
       self._employees = {}  # key: employee_id, value: Employee object
   def create(self, employee):
       """Add a new employee. Duplicate IDs are not allowed."""
       if employee.employee_id in self._employees:
           raise ValueError(f"Employee with id {employee.employee_id} already exists")
       self._employees[employee.employee_id] = employee
       return employee
   def get_by_id(self, employee_id):
       """Return the employee, or None if the ID does not exist."""
       return self._employees.get(employee_id)
   def get_all(self):
       """Return a list of all employees."""
       return list(self._employees.values())
   def update(self, employee_id, **changes):
       """Update the given fields. Returns the employee, or None if not found."""
       employee = self.get_by_id(employee_id)
       if employee is None:
           return None
       unknown = set(changes) - self.ALLOWED_FIELDS
       if unknown:
           raise ValueError(f"Unknown field(s): {', '.join(sorted(unknown))}")
       # Salary is checked first, so a bad salary changes nothing at all
       if "salary" in changes:
           employee.update_salary(changes["salary"])
       for field in ("name", "email", "department", "status"):
           if field in changes:
               setattr(employee, field, changes[field])
       return employee
   def delete(self, employee_id):
       """Remove the employee. Returns True if deleted, False if not found."""
       if employee_id not in self._employees:
           return False
       del self._employees[employee_id]
       return True
   