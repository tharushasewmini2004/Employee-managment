# Performance Investigation – Day 5 Hard Scenario

**Scenario:** `GET /employees` works with 20 records but becomes slow with
2 million records. How would I investigate before changing the code?

**Principle:** measure first, find the real bottleneck, then change one thing
at a time and measure again. Guessing often "optimises" the wrong part.

## Step 1 – Reproduce and measure

- Load a realistic amount of data (2 million rows) into a test or staging
  database, never into production.
- Use the structured logs: every request already logs `duration_ms` and a
  `request_id`, so I can see which requests are slow and how slow.
- Look at percentiles (p50, p95, p99), not only the average: a few very slow
  requests can hide behind a good average.
- Split the time: how much is spent **in the database** and how much **in
  Python** (building objects and JSON)? This decides where to look next.

## Step 2 – Checklist

| Area | What I would check | How / tool |
|---|---|---|
| **Pagination** | Is the endpoint returning all rows? (This API already paginates with `page` and `size`, max 100.) Deep pages use `OFFSET`, and PostgreSQL still reads and skips all earlier rows, so page 50,000 is slow. `COUNT(*)` for `total` also scans every matching row. | Compare `duration_ms` for page 1 and a very deep page. If deep pages are slow, consider **keyset (cursor) pagination**: `WHERE employee_id > last_seen_id ORDER BY employee_id LIMIT 20`. Consider an estimated or cached total. |
| **SQL query performance** | Which SQL statements run, and how long each one takes. | Turn on SQLAlchemy SQL logging in a test environment (`echo=True`), PostgreSQL's `log_min_duration_statement`, and the `pg_stat_statements` extension to list the slowest queries. |
| **Indexes** | Are the filter and sort columns indexed? PostgreSQL indexes primary keys and unique columns automatically (`employee_id`, `email`), but **not** foreign keys such as `department_id`, nor `status`, `salary` or `deleted_at`. | Check the table's indexes in pgAdmin. Candidates: an index on `department_id`, on `salary`, and a **partial index** `WHERE deleted_at IS NULL`, because every query filters out soft-deleted rows. Indexes also slow down writes, so only add what the plans show is needed. |
| **Execution plans** | How PostgreSQL actually runs the query. | `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` in pgAdmin. Look for `Seq Scan` on the large table (reads every row), large `Sort` steps, and big differences between estimated and actual row counts (run `ANALYZE` to refresh statistics). |
| **Number of database calls** | The **N+1 problem**: one query for the list, plus one extra query **per employee** (for example, to load each employee's department). 100 employees would mean 101 queries. | Count the SQL statements per request in the SQL log. Fix with `selectinload()` / `joinedload()` or a join, so related data loads in one query. |
| **Serialization** | Turning thousands of ORM objects into Pydantic models and JSON costs CPU time. | Profile the endpoint (`cProfile`, `py-spy`). Keep page sizes small, select only the needed columns, and return smaller responses. |
| **Caching** | Is the same data read again and again? Departments and total counts change rarely. | Measure how often the same query repeats. Cache rarely-changing results (e.g. Redis or in-memory with a short expiry) and clear the cache when data changes. Caching hides problems, so fix slow queries first. |
| **Connection pooling** | Requests may be waiting for a free database connection, not for the query. This API uses `pool_size=5` and `max_overflow=10`. Opening a new connection is slow (the first request after start-up took about 2.4 seconds in my logs, later ones about 16 ms). | Check `pg_stat_activity` in PostgreSQL and the pool's waiting time. If all connections are busy, tune the pool size, make queries faster, or add a pooler such as PgBouncer. |
| **Monitoring** | Is the problem constant, or only at busy times? Did it start after a release? | Dashboards for request latency (p95/p99), error rate and requests per second; database CPU, memory and slow-query logs; tracing (e.g. OpenTelemetry) to show time spent in each layer; alerts when latency is too high. The `request_id` connects a slow request to its log lines. |

## Step 3 – Change, then measure again

1. Fix the biggest measured bottleneck first (usually a missing index, an
   N+1 query, or deep `OFFSET` pagination).
2. Change **one thing at a time**, and compare the same measurements before
   and after.
3. Add a performance test with large data so the problem cannot come back
   unnoticed.

## Likely findings for this API

- `OFFSET` pagination and `COUNT(*)` become slow on deep pages with 2 million rows.
- `department_id`, `status`, `salary` and `deleted_at` have no indexes, so
  filtered queries use sequential scans.
- These would be confirmed with `EXPLAIN ANALYZE` before adding indexes or
  switching to keyset pagination.
  # Performance Investigation – Day 5 Hard Scenario

**Scenario:** `GET /employees` works with 20 records but becomes slow with
2 million records. How would I investigate before changing the code?

**Principle:** measure first, find the real bottleneck, then change one thing
at a time and measure again. Guessing often "optimises" the wrong part.

## Step 1 – Reproduce and measure

- Load a realistic amount of data (2 million rows) into a test or staging
  database, never into production.
- Use the structured logs: every request already logs `duration_ms` and a
  `request_id`, so I can see which requests are slow and how slow.
- Look at percentiles (p50, p95, p99), not only the average: a few very slow
  requests can hide behind a good average.
- Split the time: how much is spent **in the database** and how much **in
  Python** (building objects and JSON)? This decides where to look next.

## Step 2 – Checklist

| Area | What I would check | How / tool |
|---|---|---|
| **Pagination** | Is the endpoint returning all rows? (This API already paginates with `page` and `size`, max 100.) Deep pages use `OFFSET`, and PostgreSQL still reads and skips all earlier rows, so page 50,000 is slow. `COUNT(*)` for `total` also scans every matching row. | Compare `duration_ms` for page 1 and a very deep page. If deep pages are slow, consider **keyset (cursor) pagination**: `WHERE employee_id > last_seen_id ORDER BY employee_id LIMIT 20`. Consider an estimated or cached total. |
| **SQL query performance** | Which SQL statements run, and how long each one takes. | Turn on SQLAlchemy SQL logging in a test environment (`echo=True`), PostgreSQL's `log_min_duration_statement`, and the `pg_stat_statements` extension to list the slowest queries. |
| **Indexes** | Are the filter and sort columns indexed? PostgreSQL indexes primary keys and unique columns automatically (`employee_id`, `email`), but **not** foreign keys such as `department_id`, nor `status`, `salary` or `deleted_at`. | Check the table's indexes in pgAdmin. Candidates: an index on `department_id`, on `salary`, and a **partial index** `WHERE deleted_at IS NULL`, because every query filters out soft-deleted rows. Indexes also slow down writes, so only add what the plans show is needed. |
| **Execution plans** | How PostgreSQL actually runs the query. | `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` in pgAdmin. Look for `Seq Scan` on the large table (reads every row), large `Sort` steps, and big differences between estimated and actual row counts (run `ANALYZE` to refresh statistics). |
| **Number of database calls** | The **N+1 problem**: one query for the list, plus one extra query **per employee** (for example, to load each employee's department). 100 employees would mean 101 queries. | Count the SQL statements per request in the SQL log. Fix with `selectinload()` / `joinedload()` or a join, so related data loads in one query. |
| **Serialization** | Turning thousands of ORM objects into Pydantic models and JSON costs CPU time. | Profile the endpoint (`cProfile`, `py-spy`). Keep page sizes small, select only the needed columns, and return smaller responses. |
| **Caching** | Is the same data read again and again? Departments and total counts change rarely. | Measure how often the same query repeats. Cache rarely-changing results (e.g. Redis or in-memory with a short expiry) and clear the cache when data changes. Caching hides problems, so fix slow queries first. |
| **Connection pooling** | Requests may be waiting for a free database connection, not for the query. This API uses `pool_size=5` and `max_overflow=10`. Opening a new connection is slow (the first request after start-up took about 2.4 seconds in my logs, later ones about 16 ms). | Check `pg_stat_activity` in PostgreSQL and the pool's waiting time. If all connections are busy, tune the pool size, make queries faster, or add a pooler such as PgBouncer. |
| **Monitoring** | Is the problem constant, or only at busy times? Did it start after a release? | Dashboards for request latency (p95/p99), error rate and requests per second; database CPU, memory and slow-query logs; tracing (e.g. OpenTelemetry) to show time spent in each layer; alerts when latency is too high. The `request_id` connects a slow request to its log lines. |

## Step 3 – Change, then measure again

1. Fix the biggest measured bottleneck first (usually a missing index, an
   N+1 query, or deep `OFFSET` pagination).
2. Change **one thing at a time**, and compare the same measurements before
   and after.
3. Add a performance test with large data so the problem cannot come back
   unnoticed.

## Likely findings for this API

- `OFFSET` pagination and `COUNT(*)` become slow on deep pages with 2 million rows.
- `department_id`, `status`, `salary` and `deleted_at` have no indexes, so
  filtered queries use sequential scans.
- These would be confirmed with `EXPLAIN ANALYZE` before adding indexes or
  switching to keyset pagination.