# app/services.py
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Department, Employee, Leave
from app.repositories import DepartmentRepository, EmployeeRepository, LeaveRepository
from app.schemas import DepartmentCreate, EmployeeCreate, EmployeeUpdate, LeaveCreate


# ---------- Business errors (the API turns these into status codes in Part 5) ----------
class NotFoundError(Exception):
    """The requested record does not exist."""


class DuplicateError(Exception):
    """A value that must be unique is already used."""


class InvalidReferenceError(Exception):
    """A foreign key points to a record that does not exist (e.g. department_id=999)."""


# ---------- Transactions ----------
@contextmanager
def transaction(db: Session, conflict_message: str):
    """All database changes inside this block succeed together or fail together."""
    try:
        yield
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateError(conflict_message) from None
    except Exception:
        db.rollback()
        raise


# ---------- Departments ----------
class DepartmentService:
    def __init__(self, db: Session):
        self.db = db
        self.departments = DepartmentRepository(db)

    def list_departments(self):
        return self.departments.get_all()

    def create_department(self, data: DepartmentCreate):
        message = f"Department '{data.department_name}' already exists"
        if self.departments.get_by_name(data.department_name):
            raise DuplicateError(message)
        with transaction(self.db, message):
            department = self.departments.add(
                Department(department_name=data.department_name)
            )
        return department


# ---------- Employees and leave ----------
class EmployeeService:
    def __init__(self, db: Session):
        self.db = db
        self.employees = EmployeeRepository(db)
        self.departments = DepartmentRepository(db)
        self.leaves = LeaveRepository(db)

    # --- checks used by several methods ---
    def _check_department_exists(self, department_id):
        if self.departments.get_by_id(department_id) is None:
            raise InvalidReferenceError(f"Department {department_id} does not exist")

    def _check_email_free(self, email, current_employee_id=None):
        existing = self.employees.get_by_email(email)
        if existing is not None and existing.employee_id != current_employee_id:
            raise DuplicateError(f"Email {email} is already used")

    # --- employees ---
    def list_employees(self, department_id=None, status=None, min_salary=None):
        status_value = status.value if status else None
        return self.employees.get_all(department_id, status_value, min_salary)

    def get_employee(self, employee_id):
        employee = self.employees.get_by_id(employee_id)
        if employee is None:
            raise NotFoundError(f"Employee {employee_id} not found")
        return employee

    def create_employee(self, data: EmployeeCreate):
        self._check_department_exists(data.department_id)
        self._check_email_free(data.email)
        with transaction(self.db, f"Email {data.email} is already used"):
            employee = self.employees.add(
                Employee(
                    name=data.name,
                    email=data.email,
                    department_id=data.department_id,
                    salary=data.salary,
                    status=data.status.value,
                )
            )
        return employee

    def update_employee(self, employee_id, data: EmployeeUpdate):
        employee = self.get_employee(employee_id)
        self._check_department_exists(data.department_id)
        self._check_email_free(data.email, current_employee_id=employee_id)
        values = data.model_dump()
        values["status"] = data.status.value
        with transaction(self.db, f"Email {data.email} is already used"):
            self.employees.update(employee, values)
        return employee

    def delete_employee(self, employee_id):
        """Soft delete: hide the employee and reject their pending leave, in ONE transaction."""
        employee = self.get_employee(employee_id)
        with transaction(self.db, f"Employee {employee_id} could not be deleted"):
            self.employees.soft_delete(employee)
            for leave in self.leaves.get_for_employee(employee_id):
                if leave.status == "PENDING":
                    leave.status = "REJECTED"

    # --- leave ---
    def add_leave(self, employee_id, data: LeaveCreate):
        self.get_employee(employee_id)  # stops with NotFoundError if missing or deleted
        with transaction(self.db, "Leave record could not be saved"):
            leave = self.leaves.add(
                Leave(
                    employee_id=employee_id,
                    leave_type=data.leave_type.value,
                    start_date=data.start_date,
                    end_date=data.end_date,
                )
            )
        return leave

    def list_leave(self, employee_id):
        self.get_employee(employee_id)
        return self.leaves.get_for_employee(employee_id)
    