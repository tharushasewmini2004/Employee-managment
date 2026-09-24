# main.py
from employee_ops import (
    EMPLOYEES, print_employees, count_employees, find_highest_paid,
    calculate_average_salary, get_employees_above,
)
from string_utils import reverse_string, is_palindrome
from validation import is_valid_salary


def run_assignment_a():
    print("=== Assignment A ===")
    print_employees(EMPLOYEES)
    print("Count:", count_employees(EMPLOYEES))
    print("Highest paid:", find_highest_paid(EMPLOYEES))
    print("Average salary:", calculate_average_salary(EMPLOYEES))
    print("Earning > 100,000:", get_employees_above(EMPLOYEES))


def run_assignment_b():
    print("\n=== Assignment B ===")
    print('reverse_string("Hello") ->', reverse_string("Hello"))
    print('is_palindrome("madam") ->', is_palindrome("madam"))
    for test_value in [50000, -10, "abc", None, "7500"]:
        print(f"is_valid_salary({test_value!r}) ->", is_valid_salary(test_value))


def run_hard_scenario():
    print("\n=== Hard Scenario ===")
    with_none = EMPLOYEES + [{"id": 4, "name": "Sara", "salary": None}]
    print("Average with a None salary:", calculate_average_salary(with_none))
    print("Average of empty list:", calculate_average_salary([]))


if __name__ == "__main__":
    run_assignment_a()
    run_assignment_b()
    run_hard_scenario()
    if __name__ == "__main__":