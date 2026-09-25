# employee.py

from validation import is_valid_salary


class Employee:

    """One employee in the company (business layer - no database or API)."""

    def __init__(self, employee_id, name, email, salary, department, status="active"):

        self.employee_id = employee_id

        self.name = name

        self.email = email

        self.salary = self._check_salary(salary)

        self.department = department

        self.status = status

    @staticmethod

    def _check_salary(salary):

        """Return the salary as a number, or raise ValueError if it is invalid."""

        if not is_valid_salary(salary):

            raise ValueError(f"Invalid salary: {salary!r}. Salary must be a number and not negative.")

        return float(salary)

    def get_details(self):

        """Return all employee information as a dictionary."""

        return {

            "employee_id": self.employee_id,

            "name": self.name,

            "email": self.email,

            "salary": self.salary,

            "department": self.department,

            "status": self.status,

        }

    def calculate_annual_salary(self):

        """Salary is stored as a monthly amount, so annual = 12 months."""

        return self.salary * 12

    def update_salary(self, new_salary):

        """Change the salary. Invalid values are rejected and the old salary is kept."""

        self.salary = self._check_salary(new_salary)

    def __repr__(self):

        return f"Employee(id={self.employee_id}, name={self.name!r}, salary={self.salary})"
 