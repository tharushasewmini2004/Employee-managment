# app/repositories.py
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Department, Employee, Leave


class DepartmentRepository:
    """All database queries for departments."""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        query = select(Department).order_by(Department.department_id)
        return list(self.db.scalars(query))

    def get_by_id(self, department_id):
        return self.db.get(Department, department_id)

    def get_by_name(self, department_name):
        query = select(Department).where(
            func.lower(Department.department_name) == department_name.lower()
        )
        return self.db.scalar(query)

    def add(self, department):
        self.db.add(department)
        self.db.flush()  # sends the INSERT so the new ID exists, but does NOT commit
        return department


class EmployeeRepository:
    """All database queries for employees. Soft-deleted employees are hidden."""

    def __init__(self, db: Session):
        self.db = db

    def _not_deleted(self):
        return select(Employee).where(Employee.deleted_at.is_(None))

    def get_all(self, department_id=None, status=None, min_salary=None):
        query = self._not_deleted()
        if department_id is not None:
            query = query.where(Employee.department_id == department_id)
        if status is not None:
            query = query.where(Employee.status == status)
        if min_salary is not None:
            query = query.where(Employee.salary >= min_salary)
        return list(self.db.scalars(query.order_by(Employee.employee_id)))

    def get_by_id(self, employee_id):
        query = self._not_deleted().where(Employee.employee_id == employee_id)
        return self.db.scalar(query)

    def get_by_email(self, email):
        # Includes soft-deleted employees, because the email column is unique for every row
        query = select(Employee).where(func.lower(Employee.email) == email.lower())
        return self.db.scalar(query)

    def add(self, employee):
        self.db.add(employee)
        self.db.flush()
        return employee

    def update(self, employee, data):
        for field, value in data.items():
            setattr(employee, field, value)
        self.db.flush()
        return employee

    def soft_delete(self, employee):
        employee.deleted_at = datetime.now(timezone.utc)
        self.db.flush()


class LeaveRepository:
    """All database queries for leave records."""

    def __init__(self, db: Session):
        self.db = db

    def get_for_employee(self, employee_id):
        query = (
            select(Leave)
            .where(Leave.employee_id == employee_id)
            .order_by(Leave.start_date)
        )
        return list(self.db.scalars(query))

    def add(self, leave):
        self.db.add(leave)
        self.db.flush()
        return leave
    