import pytest

from core.expense import (
    create_expense,
    list_expenses_for_user,
    approve_expense,
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
        "spent_at": "2026-01-20",
    }


def test_create_expense_success(store):
    e = create_expense(store, valid_payload())
    assert e["expense_id"]
    assert e["status"] == "submitted"
    assert e["user_id"] == "user_1"
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


def test_list_expenses_for_user_returns_only_that_user(store):
    create_expense(store, valid_payload(user_id="user_1", amount=10))
    create_expense(store, valid_payload(user_id="user_2", amount=20))

    res = list_expenses_for_user(store, "user_1")
    assert len(res) == 1
    assert res[0]["user_id"] == "user_1"


def test_list_expenses_for_user_empty_when_none(store):
    res = list_expenses_for_user(store, "user_3")
    assert res == []


def test_approve_submitted_expense_success(store):
    e = create_expense(store, valid_payload(user_id="user_1"))
    updated = approve_expense(store, e["expense_id"], "manager_1")
    assert updated["status"] == "approved"
    assert updated["approved_by"] == "manager_1"


def test_cannot_approve_twice(store):
    e = create_expense(store, valid_payload(user_id="user_1"))
    approve_expense(store, e["expense_id"], "manager_1")
    with pytest.raises(ValueError) as ex:
        approve_expense(store, e["expense_id"], "manager_1")
    assert "only submitted" in str(ex.value)


def test_reject_submitted_expense_success(store):
    e = create_expense(store, valid_payload(user_id="user_2"))
    updated = reject_expense(store, e["expense_id"], "manager_1", "Receipt missing")
    assert updated["status"] == "rejected"
    assert updated["rejected_by"] == "manager_1"
    assert updated["rejection_reason"] == "Receipt missing"


def test_reject_requires_reason(store):
    e = create_expense(store, valid_payload(user_id="user_2"))
    with pytest.raises(ValueError) as ex:
        reject_expense(store, e["expense_id"], "manager_1", "   ")
    assert "reason" in str(ex.value).lower()
