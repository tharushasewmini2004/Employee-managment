# tests/test_api.py
"""API / integration tests: real HTTP requests go through FastAPI, the service layer,
the repositories and the (in-memory test) database."""
from app.models import Leave


# ---------- Helpers ----------
def create_department(client, name="IT"):
    response = client.post("/departments", json={"department_name": name})
    assert response.status_code == 201
    return response.json()["department_id"]


def employee_body(department_id, **changes):
    body = {
        "name": "Sara",
        "email": "sara@company.com",
        "department_id": department_id,
        "salary": 85000,
        "status": "ACTIVE",
    }
    body.update(changes)
    return body


def create_employee(client, **changes):
    department_id = create_department(client)
    response = client.post("/employees", json=employee_body(department_id, **changes))
    assert response.status_code == 201
    return response.json()


# ---------- Employee creation ----------
def test_create_employee(client):
    department_id = create_department(client)
    response = client.post("/employees", json=employee_body(department_id))
    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] > 0
    assert data["name"] == "Sara"
    assert data["salary"] == 85000
    assert data["status"] == "ACTIVE"
    assert "created_at" in data


# ---------- Retrieving ----------
def test_get_employee(client):
    employee = create_employee(client)
    response = client.get(f"/employees/{employee['employee_id']}")
    assert response.status_code == 200
    assert response.json()["email"] == "sara@company.com"


def test_list_employees_is_paginated(client):
    department_id = create_department(client)
    for i in range(3):
        client.post("/employees", json=employee_body(
            department_id, name=f"Employee {i}", email=f"emp{i}@company.com"))
    response = client.get("/employees", params={"page": 1, "size": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2


# ---------- Update and delete ----------
def test_update_employee(client):
    employee = create_employee(client)
    body = employee_body(employee["department_id"], salary=95000)
    response = client.put(f"/employees/{employee['employee_id']}", json=body)
    assert response.status_code == 200
    assert response.json()["salary"] == 95000


def test_delete_employee(client):
    employee = create_employee(client)
    url = f"/employees/{employee['employee_id']}"
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404  # hidden after soft delete


def test_delete_rejects_pending_leave_in_same_transaction(client, db_session):
    employee = create_employee(client)
    leave = client.post(f"/employees/{employee['employee_id']}/leave", json={
        "leave_type": "ANNUAL", "start_date": "2026-12-01", "end_date": "2026-12-03"})
    assert leave.status_code == 201
    client.delete(f"/employees/{employee['employee_id']}")
    assert db_session.get(Leave, leave.json()["leave_id"]).status == "REJECTED"


# ---------- Invalid employee ID ----------
def test_get_unknown_employee_returns_404(client):
    response = client.get("/employees/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee 9999 not found"}


def test_update_and_delete_unknown_employee_return_404(client):
    department_id = create_department(client)
    assert client.put("/employees/9999", json=employee_body(department_id)).status_code == 404
    assert client.delete("/employees/9999").status_code == 404


def test_non_numeric_employee_id_returns_422(client):
    assert client.get("/employees/abc").status_code == 422


# ---------- Invalid salary ----------
def test_negative_salary_returns_422(client):
    department_id = create_department(client)
    response = client.post("/employees", json=employee_body(department_id, salary=-500))
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "salary"]


def test_text_salary_returns_422(client):
    department_id = create_department(client)
    response = client.post("/employees", json=employee_body(department_id, salary="abc"))
    assert response.status_code == 422


# ---------- Duplicate email ----------
def test_duplicate_email_returns_409(client):
    department_id = create_department(client)
    assert client.post("/employees", json=employee_body(department_id)).status_code == 201
    response = client.post("/employees", json=employee_body(
        department_id, name="Other", email="SARA@company.com"))
    assert response.status_code == 409
    assert "already used" in response.json()["detail"]


# ---------- Missing required fields ----------
def test_missing_required_fields_return_422(client):
    response = client.post("/employees", json={"name": "John", "salary": "abc"})
    assert response.status_code == 422
    fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"email", "department_id", "salary"} <= fields


def test_missing_department_returns_422(client):
    response = client.post("/employees", json=employee_body(999))
    assert response.status_code == 422
    assert response.json() == {"detail": "Department 999 does not exist"}
