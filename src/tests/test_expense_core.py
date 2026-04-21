from datetime import date, timedelta

import pytest

from core.expense import (
    approve_expense,
    create_expense,
    list_expenses_for_user,
    reject_expense,
)


@pytest.fixture
def store():
    return []


def valid_payload(user_id="user_1", amount=100):
    return {
        "user_id": user_id,
        "amount": amount,
        "currency": "EUR",
        "category": "travel",
        "description": "Taxi",
        "expense_date": "2026-01-20",
    }


def test_create_expense_success(store):
    expense = create_expense(store, valid_payload())
    assert expense["expense_id"]
    assert expense["status"] == "submitted"
    assert expense["user_id"] == "user_1"
    assert expense["expense_date"] == "2026-01-20"
    assert expense["history"][0]["action"] == "submitted"
    assert len(store) == 1


@pytest.mark.parametrize("bad_amount", [0, -1, True, "100"])
def test_create_expense_invalid_amount_raises(store, bad_amount):
    payload = valid_payload()
    payload["amount"] = bad_amount
    with pytest.raises(ValueError):
        create_expense(store, payload)


def test_create_expense_missing_field_raises(store):
    payload = valid_payload()
    payload.pop("currency")
    with pytest.raises(ValueError) as ex:
        create_expense(store, payload)
    assert "currency is required" in str(ex.value)


def test_create_expense_future_date_raises(store):
    payload = valid_payload()
    payload["expense_date"] = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValueError) as ex:
        create_expense(store, payload)
    assert "future" in str(ex.value)


def test_list_expenses_for_user_returns_only_that_user(store):
    create_expense(store, valid_payload(user_id="user_1", amount=10))
    create_expense(store, valid_payload(user_id="user_2", amount=20))

    result = list_expenses_for_user(store, "user_1")
    assert len(result) == 1
    assert result[0]["user_id"] == "user_1"


def test_approve_submitted_expense_success(store):
    expense = create_expense(store, valid_payload(user_id="user_1"))
    updated = approve_expense(store, expense["expense_id"], "manager_1")
    assert updated["status"] == "approved"
    assert updated["decided_by"] == "manager_1"
    assert updated["history"][-1]["to_status"] == "approved"


def test_cannot_approve_twice(store):
    expense = create_expense(store, valid_payload(user_id="user_1"))
    approve_expense(store, expense["expense_id"], "manager_1")
    with pytest.raises(ValueError) as ex:
        approve_expense(store, expense["expense_id"], "manager_1")
    assert "only submitted" in str(ex.value)


def test_reject_submitted_expense_success(store):
    expense = create_expense(store, valid_payload(user_id="user_2"))
    updated = reject_expense(store, expense["expense_id"], "manager_1", "Receipt missing")
    assert updated["status"] == "rejected"
    assert updated["decided_by"] == "manager_1"
    assert updated["rejection_reason"] == "Receipt missing"
    assert updated["history"][-1]["to_status"] == "rejected"


def test_reject_requires_reason(store):
    expense = create_expense(store, valid_payload(user_id="user_2"))
    with pytest.raises(ValueError) as ex:
        reject_expense(store, expense["expense_id"], "manager_1", "   ")
    assert "reason" in str(ex.value).lower()
