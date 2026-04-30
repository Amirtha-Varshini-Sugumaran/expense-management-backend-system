import os

os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient

from src import models  # noqa: F401
from src.app import app
from src.db import Base, engine


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def employee_headers(user_id="emp_001"):
    return {"X-User-Id": user_id, "X-User-Role": "employee"}


def manager_headers(user_id="mgr_001"):
    return {"X-User-Id": user_id, "X-User-Role": "manager"}


def finance_headers(user_id="fin_001"):
    return {"X-User-Id": user_id, "X-User-Role": "finance"}


def valid_payload(**overrides):
    payload = {
        "amount": 42.80,
        "currency": "EUR",
        "category": "travel",
        "description": "Taxi from airport to client office",
        "expense_date": "2026-04-10",
        "receipt_name": "taxi.pdf",
    }
    payload.update(overrides)
    return payload


def create_expense(client, headers=None, **overrides):
    response = client.post(
        "/expenses",
        json=valid_payload(**overrides),
        headers=headers or employee_headers(),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health_check_returns_database_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_employee_can_submit_expense(client):
    expense = create_expense(client)
    assert expense["status"] == "submitted"
    assert expense["submitted_by"] == "emp_001"
    assert expense["history"][0]["action"] == "submitted"


def test_create_rejects_future_expense_date(client):
    response = client.post(
        "/expenses",
        json=valid_payload(expense_date="2099-01-01"),
        headers=employee_headers(),
    )
    assert response.status_code == 400
    assert "future" in response.json()["detail"]


def test_create_rejects_unknown_category(client):
    response = client.post(
        "/expenses",
        json=valid_payload(category="party"),
        headers=employee_headers(),
    )
    assert response.status_code == 400
    assert "category" in response.json()["detail"]


def test_manager_can_approve_submitted_expense(client):
    expense = create_expense(client)
    response = client.post(
        f"/expenses/{expense['expense_id']}/approve",
        json={"manager_comment": "Within travel policy"},
        headers=manager_headers(),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "approved"
    assert body["decided_by"] == "mgr_001"
    assert body["history"][-1]["to_status"] == "approved"


def test_employee_cannot_approve_expense(client):
    expense = create_expense(client)
    response = client.post(
        f"/expenses/{expense['expense_id']}/approve",
        json={},
        headers=employee_headers("emp_002"),
    )
    assert response.status_code == 403


def test_user_cannot_self_approve(client):
    expense = create_expense(client)
    response = client.post(
        f"/expenses/{expense['expense_id']}/approve",
        json={},
        headers=manager_headers("emp_001"),
    )
    assert response.status_code == 403
    assert "own expenses" in response.json()["detail"]


def test_reject_requires_reason(client):
    expense = create_expense(client)
    response = client.post(
        f"/expenses/{expense['expense_id']}/reject",
        json={"rejection_reason": "  "},
        headers=manager_headers(),
    )
    assert response.status_code == 422


def test_cannot_review_final_expense_twice(client):
    expense = create_expense(client)
    first = client.post(
        f"/expenses/{expense['expense_id']}/approve",
        json={},
        headers=manager_headers(),
    )
    assert first.status_code == 200

    second = client.post(
        f"/expenses/{expense['expense_id']}/reject",
        json={"rejection_reason": "Changed my mind"},
        headers=manager_headers(),
    )
    assert second.status_code == 409


def test_finance_can_filter_and_paginate_expenses(client):
    create_expense(client, headers=employee_headers("emp_001"), amount=10, category="travel")
    create_expense(client, headers=employee_headers("emp_002"), amount=25, category="software")
    create_expense(client, headers=employee_headers("emp_001"), amount=15, category="travel")

    response = client.get(
        "/expenses?category=travel&limit=1&offset=1&sort=amount_asc",
        headers=finance_headers(),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["amount"] == 15.0


def test_employee_list_is_scoped_to_their_own_expenses(client):
    create_expense(client, headers=employee_headers("emp_001"), amount=10)
    create_expense(client, headers=employee_headers("emp_002"), amount=20)

    response = client.get("/expenses", headers=employee_headers("emp_001"))
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["submitted_by"] == "emp_001"
