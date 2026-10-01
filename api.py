# api.py

from fastapi import FastAPI, HTTPException, Query, Response, status

from api_repository import DuplicateEmailError, InMemoryEmployeeRepository

from schemas import EmployeeCreate, EmployeeResponse, EmployeeStatus, EmployeeUpdate

app = FastAPI(title="Employee Management API", version="3.0")

repo = InMemoryEmployeeRepository()

# Sample data so the GET endpoints have something to return

for sample in [

    EmployeeCreate(name="John", email="john@company.com", department_id=1, salary=100000),

    EmployeeCreate(name="Jane", email="jane@company.com", department_id=2, salary=120000),

    EmployeeCreate(name="Mike", email="mike@company.com", department_id=2, salary=90000,

                   status=EmployeeStatus.INACTIVE),

]:

    repo.create(sample.model_dump())


def get_employee_or_404(employee_id: int) -> dict:

    """Return the employee, or stop with a 404 Not Found error."""

    employee = repo.get_by_id(employee_id)

    if employee is None:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,

                            detail=f"Employee {employee_id} not found")

    return employee


@app.get("/employees", response_model=list[EmployeeResponse])

def list_employees(

    department_id: int | None = Query(default=None, gt=0),

    employee_status: EmployeeStatus | None = Query(default=None, alias="status"),

    min_salary: float | None = Query(default=None, ge=0),

):

    """List employees, optionally filtered by department, status or minimum salary."""

    return repo.get_all(department_id=department_id, status=employee_status,

                        min_salary=min_salary)


@app.get("/employees/{employee_id}", response_model=EmployeeResponse)

def get_employee(employee_id: int):

    """Get one employee by ID."""

    return get_employee_or_404(employee_id)


@app.post("/employees", response_model=EmployeeResponse,

          status_code=status.HTTP_201_CREATED)

def create_employee(payload: EmployeeCreate):

    """Create a new employee."""

    try:

        return repo.create(payload.model_dump())

    except DuplicateEmailError:

        raise HTTPException(status_code=status.HTTP_409_CONFLICT,

                            detail=f"Email {payload.email} is already used")


@app.put("/employees/{employee_id}", response_model=EmployeeResponse)

def update_employee(employee_id: int, payload: EmployeeUpdate):

    """Replace all details of an existing employee."""

    get_employee_or_404(employee_id)

    try:

        return repo.update(employee_id, payload.model_dump())

    except DuplicateEmailError:

        raise HTTPException(status_code=status.HTTP_409_CONFLICT,

                            detail=f"Email {payload.email} is already used")


@app.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)

def delete_employee(employee_id: int):

    """Delete an employee."""

    get_employee_or_404(employee_id)

    repo.delete(employee_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
 