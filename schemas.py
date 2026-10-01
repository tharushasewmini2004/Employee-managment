# schemas.py

from datetime import datetime

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeStatus(str, Enum):

    ACTIVE = "ACTIVE"

    INACTIVE = "INACTIVE"


class EmployeeCreate(BaseModel):

    """Data the client must send to create an employee (POST)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)

    email: EmailStr

    department_id: int = Field(gt=0, strict=True)

    salary: float = Field(ge=0)

    status: EmployeeStatus = EmployeeStatus.ACTIVE


class EmployeeUpdate(EmployeeCreate):

    """PUT replaces the whole employee, so it needs the same fields as create."""


class EmployeeResponse(BaseModel):

    """What the API sends back to the client."""

    employee_id: int

    name: str

    email: EmailStr

    department_id: int

    salary: float

    status: EmployeeStatus

    created_at: datetime
 