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

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("employee_api")

app = FastAPI(title=settings.APP_NAME, version="5.0")


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
