# app/main.py
import logging
import time
import uuid

from fastapi import Depends, FastAPI, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.logging_config import setup_logging
from app.schemas import (
    DepartmentCreate,
    DepartmentResponse,
    EmployeeCreate,
    EmployeePage,
    EmployeeResponse,
    EmployeeStatus,
    EmployeeUpdate,
    ErrorResponse,
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

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("employee_api")

API_DESCRIPTION = """
REST API for managing **departments**, **employees** and **leave records**.

* Data is stored in **PostgreSQL** through SQLAlchemy.
* Employees are **soft-deleted**: hidden from the API, but kept in the database.
* `GET /employees` is **paginated** with `page` and `size`.
* Every response has an `X-Request-ID` header that matches the server logs.

All errors use the same format: `{"detail": "message"}`.
"""

TAGS = [
    {"name": "Departments", "description": "Create and list departments."},
    {"name": "Employees",
     "description": "Create, read, update, soft-delete and search employees."},
    {"name": "Leave", "description": "Leave records that belong to an employee."},
]

app = FastAPI(
    title=settings.APP_NAME,
    version="5.0",
    description=API_DESCRIPTION,
    openapi_tags=TAGS,
)

# Error responses shown in Swagger for the endpoints that can return them
NOT_FOUND = {404: {"model": ErrorResponse, "description": "Employee not found or deleted"}}
CONFLICT = {409: {"model": ErrorResponse,
                  "description": "Email or department name already used"}}


# ---------- Log every request with a request ID ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("request failed", extra={"fields": {
            "request_id": request_id, "method": request.method,
            "path": request.url.path, "status": 500, "duration_ms": duration_ms,
        }})
        raise
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info("request completed", extra={"fields": {
        "request_id": request_id, "method": request.method,
        "path": request.url.path, "status": response.status_code,
        "duration_ms": duration_ms,
    }})
    return response


# ---------- Turn errors into clean HTTP responses ----------
def error_response(request: Request, status_code: int, message: str) -> JSONResponse:
    """Log an expected error as a warning and send a clean JSON message."""
    logger.warning(message, extra={"fields": {
        "request_id": getattr(request.state, "request_id", None),
        "path": request.url.path, "status": status_code,
    }})
    return JSONResponse(status_code=status_code, content={"detail": message})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return error_response(request, 404, str(exc))


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError):
    return error_response(request, 409, str(exc))


@app.exception_handler(InvalidReferenceError)
async def invalid_reference_handler(request: Request, exc: InvalidReferenceError):
    return error_response(request, 422, str(exc))


@app.exception_handler(OperationalError)
async def database_unavailable_handler(request: Request, exc: OperationalError):
    logger.error("database unavailable", exc_info=exc, extra={"fields": {
        "request_id": getattr(request.state, "request_id", None),
    }})
    return JSONResponse(status_code=503,
                        content={"detail": "Database is unavailable. Please try again later."})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.error("unexpected error", exc_info=exc, extra={"fields": {
        "request_id": getattr(request.state, "request_id", None),
        "path": request.url.path,
    }})
    return JSONResponse(status_code=500,
                        content={"detail": "Internal server error. Please try again later."})


# ---------- Give each request a service with its own database session ----------
def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


def get_employee_service(db: Session = Depends(get_db)) -> EmployeeService:
    return EmployeeService(db)


# ---------- Departments ----------
@app.post("/departments", response_model=DepartmentResponse,
          status_code=status.HTTP_201_CREATED, tags=["Departments"],
          summary="Create a department", responses=CONFLICT)
def create_department(payload: DepartmentCreate,
                      service: DepartmentService = Depends(get_department_service)):
    """Create a new department. Department names must be unique (not case-sensitive)."""
    return service.create_department(payload)


@app.get("/departments", response_model=list[DepartmentResponse], tags=["Departments"],
         summary="List departments")
def list_departments(service: DepartmentService = Depends(get_department_service)):
    """Return all departments, sorted by ID."""
    return service.list_departments()


# ---------- Employees ----------
@app.post("/employees", response_model=EmployeeResponse,
          status_code=status.HTTP_201_CREATED, tags=["Employees"],
          summary="Create an employee", responses=CONFLICT)
def create_employee(payload: EmployeeCreate,
                    service: EmployeeService = Depends(get_employee_service)):
    """Create an employee. The department must exist (otherwise 422) and the
    email must not be used by another employee (otherwise 409)."""
    return service.create_employee(payload)


@app.get("/employees", response_model=EmployeePage, tags=["Employees"],
         summary="List employees (paginated)")
def list_employees(
    page: int = Query(default=1, ge=1, description="Page number, starting at 1"),
    size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE,
                      description="Number of employees per page"),
    department_id: int | None = Query(default=None, gt=0,
                                      description="Only this department"),
    employee_status: EmployeeStatus | None = Query(default=None, alias="status",
                                                   description="ACTIVE or INACTIVE"),
    min_salary: float | None = Query(default=None, ge=0,
                                     description="Salary greater than or equal to this"),
    service: EmployeeService = Depends(get_employee_service),
):
    """Return one page of employees (deleted employees are hidden), sorted by ID,
    with the total count and number of pages."""
    return service.list_employees(page, size, department_id, employee_status, min_salary)


@app.get("/employees/{employee_id}", response_model=EmployeeResponse, tags=["Employees"],
         summary="Get one employee", responses=NOT_FOUND)
def get_employee(employee_id: int,
                 service: EmployeeService = Depends(get_employee_service)):
    """Return one employee by ID."""
    return service.get_employee(employee_id)


@app.put("/employees/{employee_id}", response_model=EmployeeResponse, tags=["Employees"],
         summary="Update an employee", responses={**NOT_FOUND, **CONFLICT})
def update_employee(employee_id: int, payload: EmployeeUpdate,
                    service: EmployeeService = Depends(get_employee_service)):
    """Replace all details of an existing employee."""
    return service.update_employee(employee_id, payload)


@app.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT,
            tags=["Employees"], summary="Soft delete an employee", responses=NOT_FOUND)
def delete_employee(employee_id: int,
                    service: EmployeeService = Depends(get_employee_service)):
    """Hide the employee (soft delete) and reject their pending leave in one transaction."""
    service.delete_employee(employee_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Leave ----------
@app.post("/employees/{employee_id}/leave", response_model=LeaveResponse,
          status_code=status.HTTP_201_CREATED, tags=["Leave"],
          summary="Add a leave record", responses=NOT_FOUND)
def add_leave(employee_id: int, payload: LeaveCreate,
              service: EmployeeService = Depends(get_employee_service)):
    """Add a leave request for an employee. New leave starts as PENDING.
    The end date cannot be before the start date (422)."""
    return service.add_leave(employee_id, payload)


@app.get("/employees/{employee_id}/leave", response_model=list[LeaveResponse],
         tags=["Leave"], summary="List an employee's leave", responses=NOT_FOUND)
def list_leave(employee_id: int,
               service: EmployeeService = Depends(get_employee_service)):
    """Return all leave records of one employee, sorted by start date."""
    return service.list_leave(employee_id)
