# employee_ops.py
from validation import is_valid_salary

EMPLOYEES = [
    {"id": 1, "name": "John", "salary": 100000},
    {"id": 2, "name": "Jane", "salary": 120000},
    {"id": 3, "name": "Mike", "salary": 90000},
]


def print_employees(employees):
    """Print every employee on its own line."""
    if not employees:
        print("No employees found.")
        return
    for emp in employees:
        print(f"ID: {emp['id']} | Name: {emp['name']} | Salary: {emp['salary']}")


def count_employees(employees):
    """Return how many employees there are."""
    return len(employees)


def get_valid_salary_employees(employees):
    """Helper: keep only employees whose salary is valid (skips None, text, negatives)."""
    return [emp for emp in employees if is_valid_salary(emp.get("salary"))]


def find_highest_paid(employees):
    """Return the employee with the highest salary, or None if nobody has a valid salary."""
    valid = get_valid_salary_employees(employees)
    if not valid:
        return None
    return max(valid, key=lambda emp: float(emp["salary"]))


def calculate_average_salary(employees):
    """Return the average of all valid salaries.
    Employees with an invalid salary (e.g. None) are skipped.
    Returns None if the list is empty or no salary is valid."""
    valid = get_valid_salary_employees(employees)
    if not valid:
        return None
    total = sum(float(emp["salary"]) for emp in valid)
    return total / len(valid)


def get_employees_above(employees, threshold=100000):
    """Return employees earning MORE than threshold (strictly greater)."""
    valid = get_valid_salary_employees(employees)
    return [emp for emp in valid if float(emp["salary"]) > threshold]