# Expense Management Backend System

Expense Management Backend System (EMBS) is a FastAPI backend for submitting, reviewing, approving, rejecting, and auditing employee expenses. It replaces spreadsheet- and email-based expense handling with a structured API, PostgreSQL persistence, explicit workflow rules, and test coverage around the core business behavior.

The system is intentionally compact, but it is organized like a maintainable internal service: the API layer handles HTTP concerns, repository functions own persisted workflow behavior, domain logic is covered by focused tests, and local infrastructure is reproducible with Docker Compose.

## Project Overview

EMBS supports the operational lifecycle of employee expense records.

Key capabilities:

- Submit expenses with category, amount, currency, expense date, description, and optional receipt metadata
- Validate required fields, allowed categories, allowed currencies, positive amounts, and future-dated expenses
- Store expenses and audit history in PostgreSQL through SQLAlchemy models
- Review expenses with role-aware employee, manager, and finance behavior
- Approve or reject submitted expenses while preventing duplicate final-state decisions
- List expenses with filtering, pagination, sorting, and user scoping
- Seed deterministic demo data for local walkthroughs and API exploration
- Run API and domain tests without requiring a local PostgreSQL container

## Architecture

The application follows a layered backend architecture. FastAPI receives requests, Pydantic validates payloads, repository functions enforce persisted workflow behavior, SQLAlchemy stores records, and the API serves operational consumers.

Batch ETL, streaming events, and dbt models are not runtime dependencies in the current MVP. They are documented as deliberate extension points for finance reporting, audit analytics, and long-term data maintainability.

```mermaid
flowchart LR
    A["Expense Sources\nAPI clients, finance imports, forms"] --> B["Ingestion Layer\nFastAPI endpoints"]
    B --> C["Processing Layer\nPydantic validation and workflow rules"]
    C --> D["Storage Layer\nPostgreSQL expenses and audit history"]
    D --> E["Transformation Layer\ndbt-ready finance models"]
    D --> F["Serving Layer\nFastAPI operational endpoints"]
    E --> G["Analytics Consumers\nFinance dashboards and audit reports"]
    F --> H["Operational Consumers\nEmployees, managers, finance users"]
```

End-to-end explanation:

1. A client submits an expense or review action through the FastAPI service.
2. Pydantic request models validate the shape of incoming data.
3. Repository logic enforces business rules such as allowed categories, valid dates, submitted-only reviews, and role-based access.
4. SQLAlchemy persists expenses and audit-history entries to PostgreSQL.
5. List and detail endpoints serve filtered operational views back to employees, managers, and finance users.
6. Future dbt models can transform persisted expense records into finance marts and data quality reports.

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| API | FastAPI | HTTP routing, OpenAPI docs, request handling |
| Validation | Pydantic | Request and response schemas |
| Domain logic | Python | Expense workflow rules and authorization checks |
| Persistence | SQLAlchemy | ORM models, sessions, and repository access |
| Database | PostgreSQL | Durable local and production-style storage |
| Local infrastructure | Docker Compose | Reproducible PostgreSQL service |
| Testing | pytest, FastAPI TestClient, SQLite | API and domain verification |
| Transformation extension | dbt | Future finance reporting models and data tests |
| Streaming extension | Kafka or Redpanda | Future workflow events and audit analytics |

## Data Flow

1. **Ingestion**
   Expenses enter through `POST /expenses`. The API also supports approval and rejection events through workflow-specific endpoints.

2. **Processing**
   The service validates payloads, normalizes values, enforces role-aware access rules, and prevents invalid state transitions.

3. **Storage**
   Accepted expenses and audit-history records are written to PostgreSQL. Local database connectivity is controlled through `DATABASE_URL`.

4. **Transformation**
   dbt is not included yet. Recommended future models include `stg_expenses`, `stg_expense_history`, `fct_expense_workflow`, and `mart_finance_spend_by_category`.

5. **Serving**
   FastAPI serves health checks, demo-user metadata, expense creation, filtered lists, expense detail, approval, and rejection. OpenAPI documentation is available at `/docs`.

## Setup Instructions

### Prerequisites

- Python 3.11 or later
- Docker Desktop
- Git
- PowerShell, Bash, or another terminal

### Environment Variables

Create a local `.env` file if you need to override defaults:

```env
DATABASE_URL=postgresql+psycopg://embs:embs@localhost:5433/embs
```

The `.env` file is ignored by Git. Tests override the database URL so they can run without PostgreSQL.

### Docker Setup

Start PostgreSQL:

```bash
docker compose up -d
```

Create tables:

```bash
python -m src.bootstrap_db
```

Seed demo data:

```bash
python -m src.seed_demo --reset
```

Stop PostgreSQL:

```bash
docker compose down
```

Reset PostgreSQL data:

```bash
docker compose down -v
```

### Local Run Steps

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
python -m uvicorn src.app:app --reload
```

Open API documentation:

```text
http://127.0.0.1:8000/docs
```

## Project Structure

```text
.
|-- docker-compose.yml      # Local PostgreSQL service
|-- demo_walkthrough.md     # Deterministic API walkthrough steps
|-- pytest.ini              # pytest configuration
|-- requirements.txt        # Python dependencies
|-- README.md               # Maintainer documentation
|-- src/
|   |-- app.py              # FastAPI routes, request/response models, role headers
|   |-- bootstrap_db.py     # Database table creation entry point
|   |-- db.py               # SQLAlchemy engine, base, and session setup
|   |-- main.py             # Small domain demo entry point
|   |-- models.py           # Expense and audit-history models
|   |-- seed_demo.py        # Rebuilds deterministic local demo data
|   |-- core/               # In-memory business logic for focused unit tests
|   |-- repositories/       # Database-backed expense workflow functions
|   |-- tests/              # API and domain tests
```

## Key Components

### ETL Pipeline

The current ingestion path is API-first rather than file-based ETL. The API extracts submitted fields from request payloads, validates and normalizes them, and loads accepted records into PostgreSQL. A future batch ETL command can reuse the same validation and repository rules for CSV imports or accounting-system exports.

### Streaming Pipeline

Streaming is not implemented in this MVP. The natural extension is to publish events after expense creation, approval, rejection, and audit-history writes. Topics such as `expense.created`, `expense.approved`, and `expense.rejected` would support near-real-time finance dashboards and immutable audit processing.

### dbt Models

dbt is not included yet, but the persisted expense and audit-history tables are strong sources for analytics models:

- `stg_expenses`: standardize source expense fields
- `stg_expense_history`: clean audit event records
- `fct_expense_workflow`: measure submission, approval, rejection, and review latency
- `mart_finance_spend_by_category`: aggregate spend by category, currency, status, and period
- `dq_expense_validity`: validate statuses, reviewer fields, future dates, and missing audit events

### API Layer

Primary endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check API and database connectivity |
| `GET` | `/demo/users` | Show demo identities and header usage |
| `POST` | `/expenses` | Submit a new employee expense |
| `GET` | `/expenses` | List expenses with filtering, sorting, and pagination |
| `GET` | `/expenses/{expense_id}` | View one expense with audit history |
| `POST` | `/expenses/{expense_id}/approve` | Approve a submitted expense |
| `POST` | `/expenses/{expense_id}/reject` | Reject a submitted expense with a reason |

### Data Quality Checks

Current checks include:

- Positive amount validation
- Allowed category validation
- Allowed currency validation
- Future-date rejection
- Required rejection reason
- Submitted-only approval and rejection
- Employee self-review prevention
- Employee-scoped list results
- Audit history written for workflow actions

## Testing

Run all tests:

```bash
pytest
```

Run focused test files:

```bash
pytest src/tests/test_expense_core.py
pytest src/tests/test_api.py
```

The API tests use SQLite so they do not require Docker. The application defaults to PostgreSQL for normal local runs.

## Troubleshooting

| Issue | Likely Cause | Fix |
|---|---|---|
| `connection refused` when starting the API | PostgreSQL container is not running | Run `docker compose up -d` |
| `password authentication failed` | `DATABASE_URL` does not match Docker credentials | Use `postgresql+psycopg://embs:embs@localhost:5433/embs` |
| `relation "expenses" does not exist` | Tables have not been created | Run `python -m src.bootstrap_db` |
| Demo data is stale | Database already contains older records | Run `python -m src.seed_demo --reset` |
| Port `5433` is already in use | Another local PostgreSQL service is using it | Change the host port in `docker-compose.yml` and update `DATABASE_URL` |
| Tests fail with import errors | Tests are not running from the repository root | Run `pytest` from the project root |
| Date validation fails | Expense date is missing or future-dated | Use a valid past or current `YYYY-MM-DD` date |

## Future Improvements

- Add Alembic migrations for safe schema evolution
- Replace header-based role simulation with real authentication
- Add explicit users, teams, and manager relationships
- Add receipt file upload and object storage metadata
- Add dbt models and dbt tests for finance reporting
- Emit workflow events to a streaming platform
- Add API container service to Docker Compose
- Add CI checks for tests, formatting, and dependency validation
- Add summary endpoints for finance reporting
- Add deployment configuration for a hosted environment
