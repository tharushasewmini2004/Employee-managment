# app/schemas.py
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# ---------- Fixed choices ----------
class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class LeaveType(str, Enum):
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    CASUAL = "CASUAL"


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ---------- Errors ----------
class ErrorResponse(BaseModel):
    """Shape of every error response from this API."""
    detail: str


# ---------- Departments ----------
class DepartmentCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{"department_name": "Finance"}]},
    )

    department_name: str = Field(min_length=1, max_length=100)


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department_id: int
    department_name: str


# ---------- Employees ----------
class EmployeeCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{
            "name": "Sara",
            "email": "sara@company.com",
            "department_id": 1,
            "salary": 85000,
            "status": "ACTIVE",
        }]},
    )

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    department_id: int = Field(gt=0, strict=True)
    salary: float = Field(ge=0)
    status: EmployeeStatus = EmployeeStatus.ACTIVE


class EmployeeUpdate(EmployeeCreate):
    """PUT replaces the whole employee, so it needs the same fields as create."""


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    name: str
    email: EmailStr
    department_id: int
    salary: float
    status: EmployeeStatus
    created_at: datetime


class EmployeePage(BaseModel):
    """One page of employees, plus the numbers needed to show 'Page 1 of 5'."""
    model_config = ConfigDict(from_attributes=True)

    items: list[EmployeeResponse]
    total: int
    page: int
    size: int
    pages: int


# ---------- Leave ----------
class LeaveCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "leave_type": "ANNUAL",
        "start_date": "2026-12-01",
        "end_date": "2026-12-03",
    }]})

    leave_type: LeaveType
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class LeaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    status: LeaveStatus
    