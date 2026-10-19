# Employee Management – Day 1 (Python Foundations)

Day 1 of the 5-Day Practical Backend Engineering Program.
This day covers Python only (no FastAPI, no database).

## Requirements
- Python 3.x
- No external packages (Day 1 uses only the Python standard library)

## Setup and run
```bash
python -m venv venv
venv\Scripts\activate        # Windows

python main.py
```

## Project files
- `employee_ops.py` – employee data processing functions (Assignment A)
- `string_utils.py` – `reverse_string` and `is_palindrome` (Assignment B)
- `validation.py` – salary validation (Assignment B)
- `main.py` – runs all assignments and the hard scenario
- `requirements.txt` – external packages (none for Day 1)

## Assignment A – Employee Data Processing
Each operation is a separate reusable function that takes the employee list as input:
- `print_employees(employees)` – prints all employees
- `find_highest_paid(employees)` – returns the highest-paid employee
- `calculate_average_salary(employees)` – returns the average salary
- `get_employees_above(employees, threshold=100000)` – returns employees earning more than the threshold
- `count_employees(employees)` – returns the number of employees

## Assignment B – String & Validation
- `reverse_string("Hello")` returns `"olleH"`
- `is_palindrome("madam")` returns `True` (case-insensitive)
- `is_valid_salary(value)` returns `True` only for numbers that are 0 or more.
  Invalid input (`None`, text like `"abc"`, negative numbers, `True`/`False`)
  returns `False` instead of crashing.

## Design decisions (Hard Scenario)
- **Employee with `salary=None`:** employees with a missing, non-numeric or
  negative salary are skipped when calculating the average, the highest salary
  and the salary filter. The program never crashes on bad salary data.
- **Empty employee list:** `calculate_average_salary([])` returns `None`
  instead of `0`. An average of 0 would wrongly suggest that employees earn
  nothing, while `None` clearly means "no data to calculate an average".
  `find_highest_paid([])` also returns `None` for the same reason.
- **"More than 100,000"** is treated as strictly greater, so an employee earning
  exactly 100,000 is not included.
  
  ## Author
Tharusha – Intern, Day 1 submission

# Day 2 – OOP & Application Architecture
### Files
- `employee.py` – Employee class (Assignment C)
- `employee_repository.py` – in-memory EmployeeRepository (Assignment D)
- `run_day2.py` – demo of all Day 2 features: `python run_day2.py`
- `ARCHITECTURE.md` – Hard Scenario: layered architecture and diagram
### Design decisions
- Salary is stored as a **monthly** amount, so `calculate_annual_salary()` returns salary × 12.
- Invalid salaries raise `ValueError`, so an Employee object can never hold a negative salary.
 A failed `update_salary()` keeps the old salary.
- The repository returns `None` (get/update) or `False` (delete) when an ID does not exist,
 and raises `ValueError` for duplicate IDs. 


 ## Author
Tharusha – Intern, Day 2 submission

## Day 3 – FastAPI & REST

### Run the API

```bash

pip install -r requirements.txt

uvicorn api:app --reload
## Author
Tharusha – Intern, Day 3 submission


## Day 4 – PostgreSQL & SQLAlchemy

### Architecture
FastAPI → Service Layer → Repository Layer → SQLAlchemy → PostgreSQL

| Layer | File | Responsibility |
|---|---|---|
| API (routes) | `app/main.py` | Endpoints, status codes, error handlers |
| Schemas | `app/schemas.py` | Pydantic validation and response shapes |
| Service | `app/services.py` | Business rules, foreign key and duplicate checks, transactions |
| Repository | `app/repositories.py` | All database queries (CRUD) |
| Models | `app/models.py` | Department, Employee and Leave tables and relationships |
| Database | `app/database.py` | Engine, session and connection management |

### Setup
1. Install PostgreSQL and create a database called `employee_db`.
2. Copy `.env.example` to `.env` and put in your PostgreSQL password
   (write `@` in the password as `%40`).
3. Install packages and create the tables:
```bash
python -m pip install -r requirements.txt
python create_tables.py
```
4. Run the API and open http://127.0.0.1:8000/docs
```bash
python -m uvicorn app.main:app --reload
```

### Endpoints
| Method | URL | Success | Errors |
|---|---|---|---|
| POST | /departments | 201 | 409 duplicate name, 422 |
| GET | /departments | 200 | |
| POST | /employees | 201 | 409 duplicate email, 422 invalid data or department |
| GET | /employees (filters: department_id, status, min_salary) | 200 | |
| GET | /employees/{id} | 200 | 404 |
| PUT | /employees/{id} | 200 | 404, 409, 422 |
| DELETE | /employees/{id} | 204 | 404 |
| POST | /employees/{id}/leave | 201 | 404, 422 |
| GET | /employees/{id}/leave | 200 | 404 |

### Relationships
- One department → many employees (`employees.department_id` is a foreign key)
- One employee → many leave records (`leaves.employee_id` is a foreign key)

### Day 4 Hard Scenarios

**1. A request contains department_id=999. What should happen?**
The request is rejected with **422** and the message "Department 999 does not exist",
and nothing is saved. The service layer checks that the department exists before creating
or updating an employee, so the client gets a clear message. The database foreign key
is a second safety net if a department disappears between the check and the save.

**2. Two users update the same employee nearly simultaneously. What problems could occur?**
- **Lost update:** both users read the same employee, and the second save silently
  overwrites the first user's change.
- **Race conditions on unique values:** two requests can both pass the "email is free"
  check, then both try to save the same email.

How they are handled or can be handled:
- The database **unique constraint** rejects the second email; the service catches the
  `IntegrityError`, rolls back, and returns **409** (already implemented).
- **Optimistic locking:** add a `version` column that increases on every update. An update
  only succeeds if the version has not changed since it was read; otherwise the API
  returns 409 and the user reloads and retries. SQLAlchemy supports this with `version_id_col`.
- **Pessimistic locking:** lock the row while updating with `SELECT ... FOR UPDATE`
  (`with_for_update()` in SQLAlchemy), so the second user waits.

**3. Employee creation succeeds but a related operation fails. How should the transaction behave?**
All changes must be **rolled back**, so the database is left exactly as it was before.
Related changes are atomic: they all succeed together or all fail together. The
`transaction()` block in `app/services.py` commits only if every step succeeds, and
calls `rollback()` on any error. Example: deleting an employee also rejects their
pending leave in the same transaction, so we can never end up with a deleted employee
whose leave is still waiting for approval. The client receives an error and can safely retry.

**4. Should DELETE physically remove an employee? Explain an alternative such as soft delete.**
No. Physically deleting an employee would also lose their leave history and break
references from other records, and it cannot be undone. This API uses **soft delete**:
DELETE fills the `deleted_at` column with the current time and keeps the row. Deleted
employees are hidden from every GET endpoint, but their data is kept for history,
reporting and audits, and can be restored by clearing `deleted_at`.
Trade-offs: every query must filter out deleted rows, and a deleted employee's email
stays reserved because the unique constraint still applies. For privacy rules, old
records may eventually need to be anonymised or permanently removed.

 