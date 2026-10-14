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


# ---------- Departments ----------
class DepartmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    department_name: str = Field(min_length=1, max_length=100)


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department_id: int
    department_name: str


# ---------- Employees ----------
class EmployeeCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

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


# ---------- Leave ----------
class LeaveCreate(BaseModel):
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
    