# app/main.py
from fastapi import Depends, FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeStatus,
    EmployeeUpdate,
    LeaveCreate,
    LeaveResponse,
)
from app.services import (
    DepartmentService,
    DuplicateError,
    EmployeeService,
    InvalidReferenceError,
    NotFoundError,
)

app = FastAPI(title="Employee Management API", version="4.0")


# ---------- Turn business errors into HTTP responses ----------
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(InvalidReferenceError)
async def invalid_reference_handler(request: Request, exc: InvalidReferenceError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# ---------- Give each request a service with its own database session ----------
def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


def get_employee_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)


# ---------- Departments ----------
@app.post("/departments", response_model=DepartmentResponse,
          status_code=status.HTTP_201_CREATED, tags=["Departments"])
def create_department(payload: DepartmentCreate,
                      service: DepartmentService = Depends(get_department_service)):
    return service.create_department(payload)


@app.get("/departments", response_model=list[DepartmentResponse], tags=["Departments"])
def list_departments(service: DepartmentService = Depends(get_department_service)):
    return service.list_departments()


# ---------- Employees ----------
@app.post("/employees", response_model=EmployeeResponse,
          status_code=status.HTTP_201_CREATED, tags=["Employees"])
def create_employee(payload: EmployeeCreate,
                    service: EmployeeService = Depends(get_employee_service)):
    return service.create_employee(payload)


@app.get("/employees", response_model=list[EmployeeResponse], tags=["Employees"])
def list_employees(
    department_id: int | None = Query(default=None, gt=0),
    employee_status: EmployeeStatus | None = Query(default=None, alias="status"),
    min_salary: float | None = Query(default=None, ge=0),
    service: EmployeeService = Depends(get_employee_service),
):
    return service.list_employees(department_id, employee_status, min_salary)


@app.get("/employees/{employee_id}", response_model=EmployeeResponse, tags=["Employees"])
def get_employee(employee_id: int,
                 service: EmployeeService = Depends(get_employee_service)):
    return service.get_employee(employee_id)


@app.put("/employees/{employee_id}", response_model=EmployeeResponse, tags=["Employees"])
def update_employee(employee_id: int, payload: EmployeeUpdate,
                    service: EmployeeService = Depends(get_employee_service)):
    return service.update_employee(employee_id, payload)


@app.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT,
            tags=["Employees"])
def delete_employee(employee_id: int,
                    service: EmployeeService = Depends(get_employee_service)):
    service.delete_employee(employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Leave ----------
@app.post("/employees/{employee_id}/leave", response_model=LeaveResponse,
          status_code=status.HTTP_201_CREATED, tags=["Leave"])
def add_leave(employee_id: int, payload: LeaveCreate,
              service: EmployeeService = Depends(get_employee_service)):
    return service.add_leave(employee_id, payload)


@app.get("/employees/{employee_id}/leave", response_model=list[LeaveResponse],
         tags=["Leave"])
def list_leave(employee_id: int,
               service: EmployeeService = Depends(get_employee_service)):
    return service.list_leave(employee_id)
