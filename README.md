# Expense Management Backend API

A backend API for managing employee expense submissions, approvals, rejections, and audit-ready records.

## Business Problem

Many organizations still manage employee expenses through email, spreadsheets, or informal approval messages. That creates missing data, unclear approval ownership, manual follow-ups, and weak audit history.

EMBS standardizes the expense lifecycle so employees can submit expenses, managers can approve or reject them, and finance teams can review finalized records from one backend system.

## Business Value

- Reduces manual follow-up across employees, managers, and finance teams
- Keeps expense status changes controlled and traceable
- Improves data consistency for reporting and audit review
- Provides a clean backend foundation for future authentication, reporting, and cloud deployment

## Intended Users

- **Employees** - Submit business-related expenses
- **Managers** - Review, approve, or reject submitted expenses
- **Finance Teams** - Review approved and rejected expenses for compliance and reporting

## Core Features

- Create an expense
- List expenses for a user
- Approve an expense
- Reject an expense with a reason
- Health check endpoint for API and database verification

## Expense Lifecycle

- `submitted` -> `approved`
- `submitted` -> `rejected`

Rules enforced:

- Only `submitted` expenses can be approved or rejected
- Approved expenses cannot be modified
- Rejected expenses store a rejection reason for audit purposes

## Tech Stack

- **Language:** Python
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.x
- **Database:** PostgreSQL
- **Containerization:** Docker and Docker Compose
- **Testing:** Pytest
- **API Documentation:** OpenAPI / Swagger UI

## Architecture Overview

The project follows a layered backend structure:

- **API layer:** FastAPI routes and request validation
- **Business / repository layer:** Expense rules and state transitions
- **Database layer:** PostgreSQL with SQLAlchemy ORM

This keeps the code easier to test, maintain, and extend.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health and database connectivity check |
| POST | `/expenses` | Create a new expense |
| GET | `/expenses?user_id={id}` | List expenses for a user |
| POST | `/expenses/{expense_id}/approve` | Approve an expense |
| POST | `/expenses/{expense_id}/reject` | Reject an expense |

Swagger UI runs locally at:

```text
http://127.0.0.1:8000/docs
```

## Run Locally

Prerequisites:

- Python 3.12+
- Docker Desktop

Start PostgreSQL:

```bash
docker compose up -d
```

Initialize the database:

```bash
python -m src.bootstrap_db
```

Start the API server:

```bash
python -m uvicorn src.app:app --reload
```

Run tests:

```bash
pytest
```

## Repository Structure

```text
src/
|-- app.py              # FastAPI application
|-- db.py               # Database connection and session
|-- models.py           # SQLAlchemy models
|-- bootstrap_db.py     # Database initialization
|-- core/               # Core business logic
|-- repositories/       # Database access layer
|-- tests/              # Automated tests
```

## Project Status

- Core backend MVP completed
- Database integration completed
- Expense lifecycle implemented
- API tested through Swagger and Pytest

## Future Improvements

- Authentication and authorization
- Role-based access for employee, manager, and finance users
- Pagination and filtering
- Audit logs and reporting
- Cloud deployment
