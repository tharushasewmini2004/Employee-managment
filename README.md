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
