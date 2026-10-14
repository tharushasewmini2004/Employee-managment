# app/models.py
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[int] = mapped_column(primary_key=True)
    department_name: Mapped[str] = mapped_column(String(100), unique=True)

    # One department -> many employees
    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("salary >= 0", name="ck_employees_salary_non_negative"),
    )

    employee_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.department_id"))
    salary: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    department: Mapped["Department"] = relationship(back_populates="employees")
    # One employee -> many leave records
    leaves: Mapped[list["Leave"]] = relationship(back_populates="employee")


class Leave(Base):
    __tablename__ = "leaves"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_leaves_dates_in_order"),
    )

    leave_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.employee_id"))
    leave_type: Mapped[str] = mapped_column(String(30))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")

    employee: Mapped["Employee"] = relationship(back_populates="leaves")