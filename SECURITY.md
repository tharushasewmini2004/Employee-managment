# Security Design – Authentication & Authorization

## 1. Authentication vs authorization

| | Authentication | Authorization |
|---|---|---|
| Question | **Who are you?** | **What are you allowed to do?** |
| How | User proves identity (e.g. email + password), receives a signed token | Server checks the user's role and ownership before each action |
| Order | Happens first | Happens after authentication |
| Failure | `401 Unauthorized` – not logged in, or token missing/expired/invalid | `403 Forbidden` – logged in, but the role is not allowed to do this |

Example: an HR user logs in successfully (authenticated). When they try to
DELETE an employee, the API returns 403, because only ADMIN may delete
(not authorized).

## 2. Roles

| Role | Who | Purpose |
|---|---|---|
| **ADMIN** | System administrator | Full control, including deleting employees and managing departments |
| **HR** | Human resources staff | Manages employee records day to day, but cannot delete them |
| **EMPLOYEE** | Regular staff | Can see only their own data and request their own leave |

## 3. Permissions for employees

| Action | Endpoint | ADMIN | HR | EMPLOYEE |
|---|---|---|---|---|
| Create an employee | `POST /employees` | ✅ | ✅ | ❌ |
| View all employees | `GET /employees` | ✅ | ✅ | ❌ |
| View one employee | `GET /employees/{id}` | ✅ any | ✅ any | ✅ **own record only** |
| Update an employee | `PUT /employees/{id}` | ✅ | ✅ | ❌ |
| Delete an employee (soft delete) | `DELETE /employees/{id}` | ✅ | ❌ | ❌ |

## 4. Other endpoints

| Action | Endpoint | ADMIN | HR | EMPLOYEE |
|---|---|---|---|---|
| Create a department | `POST /departments` | ✅ | ❌ | ❌ |
| View departments | `GET /departments` | ✅ | ✅ | ✅ |
| Add leave | `POST /employees/{id}/leave` | ✅ | ✅ | ✅ **own only** |
| View leave | `GET /employees/{id}/leave` | ✅ | ✅ | ✅ **own only** |

## 5. Reasons for these decisions

- **Least privilege:** each role gets only the permissions it needs.
- **Only ADMIN can delete:** deleting removes an employee from the system and
  rejects their pending leave, so it is limited to the most trusted role.
- **HR cannot create departments:** the company structure is managed by ADMIN.
- **EMPLOYEE sees only their own data:** salaries and personal details of
  colleagues are private. An employee can never change their own salary.
- **Role checks AND ownership checks:** for EMPLOYEE, the role allows
  `GET /employees/{id}`, but the API must also check that `{id}` is the
  employee's own ID; otherwise it returns 403.

## 6. How it would be implemented in this FastAPI project

1. **Login:** `POST /auth/login` checks the email and a **hashed** password
   (bcrypt or argon2 – never store plain passwords) and returns a signed
   **JWT access token** containing the user ID, role and an expiry time.
2. **Authentication dependency:** every protected endpoint uses
   `Depends(get_current_user)`, which reads the `Authorization: Bearer <token>`
   header, verifies the signature and expiry, and returns `401` if anything is wrong.
3. **Authorization dependency:** `Depends(require_roles("ADMIN", "HR"))` returns
   `403` if the user's role is not in the allowed list.
4. **Ownership check:** for EMPLOYEE, the service layer compares the requested
   `employee_id` with the logged-in user's employee ID.

```python
def require_roles(*allowed_roles):
    def checker(user = Depends(get_current_user)):     # 401 if not logged in
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not allowed for your role")
        return user
    return checker

@app.delete("/employees/{employee_id}", status_code=204)
def delete_employee(employee_id: int,
                    user = Depends(require_roles("ADMIN")),   # only ADMIN
                    service: EmployeeService = Depends(get_employee_service)):
    service.delete_employee(employee_id)
```

## 7. Other security measures

- Use **HTTPS** so passwords and tokens cannot be read on the network.
- Keep the token signing key in an **environment variable**, never in the code
  (the same approach as `DATABASE_URL`).
- Give tokens a **short expiry** (e.g. 30 minutes).
- **Log** security events (failed logins, 403 responses) with the request ID,
  without ever logging passwords or tokens.
- Validate all input with Pydantic (already implemented) and use the ORM for
  queries, which prevents SQL injection.
  