import uuid

"""
Expense Management System - Core business logic (in-memory).

Store:
- `store` is a list of expense dictionaries.
- Each expense dict represents one expense record.
"""


# ---------- shared guards ----------

def validate_store(store):
    if not isinstance(store, list):
        raise ValueError("store must be a list")


def validate_user_id(user_id):
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id must be a non-empty string")
    return user_id.strip()


def validate_expense_id(expense_id):
    if not isinstance(expense_id, str) or not expense_id.strip():
        raise ValueError("expense_id must be a non-empty string")
    return expense_id.strip()


def validate_status(expense):
    status = expense.get("status")
    if status not in {"submitted", "approved", "rejected"}:
        raise ValueError("expense has invalid status")
    return status


# ---------- payload validation + normalization ----------

def validate_expense_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dictionary")

    required_fields = ["user_id", "amount", "currency", "category", "description", "spent_at"]
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"{field} is required")

    validate_user_id(payload["user_id"])

    amount = payload["amount"]
    # bool is a subclass of int in Python, so reject it explicitly
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("amount must be a number")
    if amount <= 0:
        raise ValueError("amount must be > 0")

    for field in ["currency", "category", "description", "spent_at"]:
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")


def normalize_expense_payload(payload):
    return {
        "user_id": payload["user_id"].strip(),
        "amount": float(payload["amount"]),
        "currency": payload["currency"].strip(),
        "category": payload["category"].strip(),
        "description": payload["description"].strip(),
        "spent_at": payload["spent_at"].strip(),
    }


# ---------- public operations ----------

def create_expense(store, payload):
    validate_store(store)
    validate_expense_payload(payload)

    clean = normalize_expense_payload(payload)

    expense = {
        "expense_id": str(uuid.uuid4()),
        **clean,
        "status": "submitted",
    }

    store.append(expense)
    return expense


def list_expenses_for_user(store, user_id):
    validate_store(store)
    user_id = validate_user_id(user_id)

    return [e for e in store if e.get("user_id") == user_id]


def get_expense_by_id(store, expense_id):
    validate_store(store)
    expense_id = validate_expense_id(expense_id)

    for expense in store:
        if expense.get("expense_id") == expense_id:
            return expense

    raise ValueError("expense not found")


def approve_expense(store, expense_id, acted_by_user_id):
    acted_by_user_id = validate_user_id(acted_by_user_id)

    expense = get_expense_by_id(store, expense_id)
    status = validate_status(expense)

    if status != "submitted":
        raise ValueError("only submitted expenses can be approved or rejected")

    expense["status"] = "approved"
    expense["approved_by"] = acted_by_user_id
    return expense


def reject_expense(store, expense_id, acted_by_user_id, reason):
    acted_by_user_id = validate_user_id(acted_by_user_id)

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("rejection reason must be a non-empty string")

    expense = get_expense_by_id(store, expense_id)
    status = validate_status(expense)

    if status != "submitted":
        raise ValueError("only submitted expenses can be approved or rejected")

    expense["status"] = "rejected"
    expense["rejected_by"] = acted_by_user_id
    expense["rejection_reason"] = reason.strip()
    return expense