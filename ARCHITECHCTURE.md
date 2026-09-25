# Architecture – Separating Responsibilities
## The problem
One 2,000-line file mixes HTTP routes, database queries, validation and
business logic. It is hard to read, hard to test, and one change can break
something unrelated. Several developers cannot work on it at the same time.
## The solution: layered architecture
Split the file by responsibility. Each layer has one job and only talks
to the layer directly below it.
| Layer | Responsibility | Example file |
|---|---|---|
| Routes (API layer) | Receive HTTP requests, return responses and status codes. No business logic. | `routes/employees.py` |
| Schemas (validation) | Check the shape and types of incoming data (Pydantic). | `schemas/employee.py` |
| Services (business logic) | Business rules, e.g. salary cannot be negative, email must be unique. | `services/employee_service.py` |
| Repositories (data access) | All database queries. Nothing else touches the database. | `repositories/employee_repository.py` |
| Models | Database tables (SQLAlchemy). | `models/employee.py` |
## Diagram
"""mermaid
flowchart TD
   C[Client / Browser] --> R[Routes - API layer]
   R --> S[Schemas - validation]
   R --> SV[Services - business logic]
   SV --> RP[Repositories - data access]
   RP --> DB[(PostgreSQL database)]
"""
Simple text version:
   Client -> Routes -> Services -> Repositories -> Database
                |
             Schemas (validate input)
## How I would split the 2,000-line file
1. Read the file and label each block: route, validation, business rule, or query.
2. Move every database query into repository classes first (lowest risk).
3. Move business rules into service classes that call the repositories.
4. Move input validation into Pydantic schemas.
5. Keep the routes thin: validate input, call a service, return the result.
6. Add tests after each move so nothing breaks, and commit step by step.
## Benefits
- Each file is small and easy to understand.
- The database can change (in-memory -> PostgreSQL) without changing the routes.
- Business logic can be tested without running a web server.
- Team members can work on different layers at the same time.
## How Day 2 already follows this
- "Employee" class holds the business rules (salary validation).
- "EmployeeRepository" is the data access layer (in memory today, PostgreSQL on Day 4).

