# tests/test_unit.py
"""Unit tests: check one piece at a time (schemas or the service layer), without HTTP."""
import pytest
from pydantic import ValidationError

from app.schemas import DepartmentCreate, EmployeeCreate, LeaveCreate
from app.services import (
    DepartmentService,
    DuplicateError,
    EmployeeService,
    InvalidReferenceError,
    NotFoundError,
)

VALID = {"name": "Sara", "email": "sara@company.com", "department_id": 1, "salary": 85000}


# ---------- Schema validation (Pydantic) ----------
def test_valid_employee_data_is_accepted():
    employee = EmployeeCreate(**VALID)
    assert employee.name == "Sara"
    assert employee.status.value == "ACTIVE"  # default value


def test_negative_salary_is_rejected():
    with pytest.raises(ValidationError):
        EmployeeCreate(**{**VALID, "salary": -1})


def test_text_salary_is_rejected():
    with pytest.raises(ValidationError):
        EmployeeCreate(**{**VALID, "salary": "abc"})


def test_empty_name_is_rejected():
    with pytest.raises(ValidationError):
        EmployeeCreate(**{**VALID, "name": "   "})


def test_missing_required_fields_are_reported():
    with pytest.raises(ValidationError) as error:
        EmployeeCreate(name="Sara")
    missing = {e["loc"][0] for e in error.value.errors() if e["type"] == "missing"}
    assert missing == {"email", "department_id", "salary"}


def test_leave_cannot_end_before_it_starts():
    with pytest.raises(ValidationError):
        LeaveCreate(leave_type="SICK", start_date="2026-11-10", end_date="2026-11-05")


# ---------- Service layer (business rules) ----------
@pytest.fixture
def department_id(db_session):
    """Create one department in the test database and return its ID."""
    department = DepartmentService(db_session).create_department(
        DepartmentCreate(department_name="IT")
    )
    return department.department_id


def test_service_creates_and_finds_employee(db_session, department_id):
    service = EmployeeService(db_session)
    created = service.create_employee(EmployeeCreate(**{**VALID, "department_id": department_id}))
    found = service.get_employee(created.employee_id)
    assert found.email == "sara@company.com"
    assert found.department.department_name == "IT"


def test_service_rejects_duplicate_email(db_session, department_id):
    service = EmployeeService(db_session)
    service.create_employee(EmployeeCreate(**{**VALID, "department_id": department_id}))
    with pytest.raises(DuplicateError):
        service.create_employee(EmployeeCreate(
            **{**VALID, "name": "Other", "email": "SARA@company.com",
               "department_id": department_id}
        ))


def test_service_rejects_missing_department(db_session):
    with pytest.raises(InvalidReferenceError):
        EmployeeService(db_session).create_employee(
            EmployeeCreate(**{**VALID, "department_id": 999})
        )


def test_service_raises_not_found_for_unknown_id(db_session):
    with pytest.raises(NotFoundError):
        EmployeeService(db_session).get_employee(9999)


def test_service_pagination(db_session, department_id):
    service = EmployeeService(db_session)
    for i in range(3):
        service.create_employee(EmployeeCreate(
            **{**VALID, "name": f"Employee {i}", "email": f"emp{i}@company.com",
               "department_id": department_id}
        ))
    page = service.list_employees(page=2, size=2)
    assert page["total"] == 3
    assert page["pages"] == 2
    assert len(page["items"]) == 1
    