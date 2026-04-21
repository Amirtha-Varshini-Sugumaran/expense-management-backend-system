# Expense Management Backend API

A FastAPI backend for submitting, reviewing, and auditing employee expenses.

The project is intentionally small, but it now behaves more like a real internal tool than a plain CRUD API: employees submit expenses, managers approve or reject them, finance can review filtered records, and every status change is captured in an audit history.

## Why This Exists

Expense approvals often start out as emails, spreadsheets, or chat messages. That works for a tiny team, but it gets messy quickly: missing receipts, unclear approval ownership, weak audit trails, and no easy way for finance to review what happened.

This API models the backend slice of that workflow.

## What It Does

- Submit expenses with category, description, currency, date, and optional receipt details
- Reject invalid expenses before they enter the workflow
- Review submitted expenses as a manager or finance user
- Prevent final expenses from being approved or rejected again
- Prevent users from approving or rejecting their own expenses
- Store approval comments, rejection reasons, timestamps, and audit history
- List expenses with filters, pagination, and sorting
- Seed a realistic demo flow for Swagger or interview walkthroughs

## Business Rules

- Amount must be greater than zero
- Expense date cannot be in the future
- Category must be one of `travel`, `meals`, `office`, `software`, `training`, `client`, or `other`
- Currency must be one of `EUR`, `GBP`, `USD`, or `INR`
- Rejections must include a reason
- Only `submitted` expenses can be approved or rejected
- Employees can only submit and view their own expenses
- Managers and finance users can review expenses, but not their own

## Architecture

```text
src/
|-- app.py                  # FastAPI routes, request/response models, role headers
|-- db.py                   # SQLAlchemy engine and session setup
|-- models.py               # Expense and expense audit-history tables
|-- bootstrap_db.py         # Creates database tables
|-- seed_demo.py            # Rebuilds demo data for walkthroughs
|-- core/                   # In-memory business logic used by unit tests
|-- repositories/           # Database-backed expense workflow
|-- tests/                  # API and domain tests
```

The route layer stays thin. Most workflow checks live in the repository layer so the API, tests, and demo data all use the same behavior.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Docker Compose
- Pytest
- Swagger / OpenAPI

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start PostgreSQL:

```bash
docker compose up -d
```

Create the tables:

```bash
python -m src.bootstrap_db
```

Seed demo data:

```bash
python -m src.seed_demo --reset
```

Start the API:

```bash
python -m uvicorn src.app:app --reload
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

## Demo Users

This project uses lightweight role simulation through request headers. It is simple on purpose and keeps the demo focused on backend workflow rules.

| Person | Header: X-User-Id | Header: X-User-Role |
|---|---|---|
| Employee | `emp_001` | `employee` |
| Second employee | `emp_002` | `employee` |
| Manager | `mgr_001` | `manager` |
| Finance reviewer | `fin_001` | `finance` |

You can also call `GET /demo/users` to see the same identities.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check API and database connectivity |
| `GET` | `/demo/users` | Show demo identities and header usage |
| `POST` | `/expenses` | Submit a new employee expense |
| `GET` | `/expenses` | List expenses with filtering and pagination |
| `GET` | `/expenses/{expense_id}` | View one expense with audit history |
| `POST` | `/expenses/{expense_id}/approve` | Approve a submitted expense |
| `POST` | `/expenses/{expense_id}/reject` | Reject a submitted expense with a reason |

Useful list filters:

```text
/expenses?status=submitted&category=travel&limit=10&offset=0&sort=submitted_at_desc
```

Supported sort values:

- `submitted_at_desc`
- `submitted_at_asc`
- `amount_desc`
- `amount_asc`
- `expense_date_desc`
- `expense_date_asc`

## Demo Flow

The seeded demo supports this walkthrough:

1. Employee `emp_001` submits a travel expense.
2. Manager `mgr_001` approves one expense with a comment.
3. Manager `mgr_001` rejects one expense with a reason.
4. Finance user `fin_001` lists approved or rejected expenses.
5. The reviewer opens one expense and shows the audit history.

See [demo_walkthrough.md](demo_walkthrough.md) for exact Swagger steps and sample request bodies.

## Run Tests

```bash
pytest
```

The API tests use SQLite so they can run without a local PostgreSQL container. The application still defaults to PostgreSQL for normal local runs.

## What This Demonstrates

- Backend workflow design beyond basic CRUD
- FastAPI request validation and OpenAPI documentation
- SQLAlchemy models and repository-style data access
- Practical role-aware authorization without overbuilding auth
- Audit/history modeling for reviewable business events
- Test coverage for validation, filtering, pagination, and invalid transitions

## Future Improvements

- Replace header role simulation with JWT authentication
- Add Alembic migrations for safe schema evolution
- Add receipt file upload/storage
- Add manager-to-employee team mapping
- Add reporting endpoints for finance summaries
- Add deployment configuration for a hosted demo
