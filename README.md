# Expense Management Backend System (EMBS)

A backend system to manage employee expenses with a structured approval and rejection workflow.

## Problem Statement

In many organizations, employee expenses are handled using emails, spreadsheets, or informal tools. This leads to:

- Missing or inconsistent expense data  
- No clear approval or rejection flow  
- Manual effort for managers and finance teams  
- Poor auditability and tracking  

As companies grow, these issues create operational delays and financial risk.

## Solution

The **Expense Management Backend System (EMBS)** provides a clean backend API that standardizes how expenses are submitted, reviewed, approved, or rejected.

This system enforces business rules, maintains a clear expense lifecycle, and stores all data reliably in a relational database.

## Intended Users

This system is designed for internal organizational use by:

- **Employees** – Submit business-related expenses  
- **Managers** – Review, approve, or reject submitted expenses  
- **Finance Teams** – Audit approved and rejected expenses for compliance and reporting  

The backend enforces clear responsibility boundaries between these roles through workflow rules.
## Core Features

- Create an expense
- List expenses for a user
- Approve an expense
- Reject an expense with a reason
- Health check endpoint for system and database verification

## Expense Lifecycle

- submitted → approved
- submitted → rejected

Rules enforced:
- Only `submitted` expenses can be approved or rejected
- Approved expenses cannot be modified
- Rejected expenses store a rejection reason for audit purposes

## High-Level Flow

1. Employee submits an expense  
2. System stores the expense with `submitted` status  
3. Manager approves or rejects the expense  
4. System updates expense status and audit fields  
5. Finance team can query finalized expense records

## Architecture Overview

The project follows a layered backend architecture:

- **API Layer** – FastAPI routes and request validation  
- **Business / Repository Layer** – Expense rules and state transitions  
- **Database Layer** – PostgreSQL with SQLAlchemy ORM  

This design improves maintainability, testability, and scalability.


## Tech Stack

- **Language:** Python 3.14  
- **Framework:** FastAPI  
- **ORM:** SQLAlchemy 2.x  
- **Database:** PostgreSQL  
- **Containerization:** Docker & Docker Compose  
- **Testing:** Pytest  
- **API Documentation:** OpenAPI (Swagger UI)

## API Endpoints

| Method | Endpoint | Description |
|------|--------|------------|
| GET | `/health` | Health and DB connectivity check |
| POST | `/expenses` | Create a new expense |
| GET | `/expenses?user_id={id}` | List expenses for a user |
| POST | `/expenses/{expense_id}/approve` | Approve an expense |
| POST | `/expenses/{expense_id}/reject` | Reject an expense |

Swagger UI:
http://127.0.0.1:8000/docs

## Running the Project Locally

### Prerequisites
- Python 3.12+ (you are using 3.14)
- Docker Desktop running

### Start PostgreSQL
```bash
docker compose up -d
```

### Initialize Database
```bash
python -m src.bootstrap_db
```

### Start API Server
```bash
python -m uvicorn src.app:app --reload
```

## Testing

Automated tests cover:
- Core expense business logic
- API endpoints

Run tests:
```bash
pytest
```

## Project Structure

src/
├── app.py              # FastAPI application
├── db.py               # Database connection and session
├── models.py           # SQLAlchemy models
├── bootstrap_db.py     # Database initialization
├── core/               # Core business logic
├── repositories/       # Database access layer
└── tests/              # Automated tests

## Project Status

- Core backend MVP completed
- Database integration completed
- Expense lifecycle fully implemented
- API tested via Swagger and Pytest

## Future Enhancements

- Authentication and authorization
- Role-based access (Employee / Manager / Finance)
- Pagination and filtering
- Audit logs and reporting
- Cloud deployment

## Purpose of This Project

This project demonstrates:

- Backend system design
- REST API development
- Business rule enforcement
- PostgreSQL integration
- Docker-based development
- Production-style project structure

## Design Decisions

- FastAPI chosen for fast iteration and strong typing
- SQLAlchemy used to enforce domain models and constraints
- Repository pattern separates business logic from persistence

## License

This project is built for learning and portfolio purposes.
