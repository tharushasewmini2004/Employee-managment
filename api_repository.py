# api_repository.py

from datetime import datetime, timezone


class DuplicateEmailError(Exception):

    """Raised when an email is already used by another employee."""


class InMemoryEmployeeRepository:

    """Stores employees as dictionaries in memory. Replaced by PostgreSQL on Day 4."""

    def __init__(self):

        self._employees = {}  # key: employee_id, value: employee dictionary

        self._next_id = 1

    def _email_taken(self, email, ignore_id=None):

        """True if another employee already uses this email (not case-sensitive)."""

        email = email.lower()

        return any(

            emp["email"].lower() == email and emp_id != ignore_id

            for emp_id, emp in self._employees.items()

        )

    def get_all(self, department_id=None, status=None, min_salary=None):

        """Return employees, filtered by any of the optional values."""

        result = list(self._employees.values())

        if department_id is not None:

            result = [e for e in result if e["department_id"] == department_id]

        if status is not None:

            result = [e for e in result if e["status"] == status]

        if min_salary is not None:

            result = [e for e in result if e["salary"] >= min_salary]

        return result

    def get_by_id(self, employee_id):

        return self._employees.get(employee_id)

    def create(self, data):

        if self._email_taken(data["email"]):

            raise DuplicateEmailError(data["email"])

        employee = {

            "employee_id": self._next_id,

            **data,

            "created_at": datetime.now(timezone.utc),

        }

        self._employees[self._next_id] = employee

        self._next_id += 1

        return employee

    def update(self, employee_id, data):

        employee = self._employees.get(employee_id)

        if employee is None:

            return None

        if self._email_taken(data["email"], ignore_id=employee_id):

            raise DuplicateEmailError(data["email"])

        employee.update(data)

        return employee

    def delete(self, employee_id):

        return self._employees.pop(employee_id, None) is not None
 
# api_repository.py

from datetime import datetime, timezone


class DuplicateEmailError(Exception):

    """Raised when an email is already used by another employee."""


class InMemoryEmployeeRepository:

    """Stores employees as dictionaries in memory. Replaced by PostgreSQL on Day 4."""

    def __init__(self):

        self._employees = {}  # key: employee_id, value: employee dictionary

        self._next_id = 1

    def _email_taken(self, email, ignore_id=None):

        """True if another employee already uses this email (not case-sensitive)."""

        email = email.lower()

        return any(

            emp["email"].lower() == email and emp_id != ignore_id

            for emp_id, emp in self._employees.items()

        )

    def get_all(self, department_id=None, status=None, min_salary=None):

        """Return employees, filtered by any of the optional values."""

        result = list(self._employees.values())

        if department_id is not None:

            result = [e for e in result if e["department_id"] == department_id]

        if status is not None:

            result = [e for e in result if e["status"] == status]

        if min_salary is not None:

            result = [e for e in result if e["salary"] >= min_salary]

        return result

    def get_by_id(self, employee_id):

        return self._employees.get(employee_id)

    def create(self, data):

        if self._email_taken(data["email"]):

            raise DuplicateEmailError(data["email"])

        employee = {

            "employee_id": self._next_id,

            **data,

            "created_at": datetime.now(timezone.utc),

        }

        self._employees[self._next_id] = employee

        self._next_id += 1

        return employee

    def update(self, employee_id, data):

        employee = self._employees.get(employee_id)

        if employee is None:

            return None

        if self._email_taken(data["email"], ignore_id=employee_id):

            raise DuplicateEmailError(data["email"])

        employee.update(data)

        return employee

    def delete(self, employee_id):

        return self._employees.pop(employee_id, None) is not None
 