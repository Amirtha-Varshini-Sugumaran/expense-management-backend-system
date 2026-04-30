from __future__ import annotations

from datetime import date
from typing import Any, Dict, List
from uuid import uuid4

from sqlalchemy.orm import Session

from src.models import Expense


# -------------------------
# Helpers
# -------------------------

def _spent_at_out(value: Any) -> Any:
    """
    Works whether the DB column is DATE (python date) or TEXT (python str).
    """
    if value is None:
        return None
    if hasattr(value, "isoformat"):  # date/datetime
        return value.isoformat()
    return str(value)  # already a string


def _to_dict(e: Expense) -> Dict[str, Any]:
    return {
        "expense_id": e.expense_id,
        "user_id": e.user_id,
        "amount": float(e.amount),
        "currency": e.currency,
        "category": e.category,
        "description": e.description,
        "spent_at": _spent_at_out(e.spent_at),
        "status": e.status,
        "approved_by": e.approved_by,
        "rejected_by": e.rejected_by,
        "rejection_reason": e.rejection_reason,
    }


def _require_non_empty(value: Any, field: str) -> None:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{field} is required")


def _get_expense_or_raise(db: Session, expense_id: str) -> Expense:
    e = db.query(Expense).filter(Expense.expense_id == expense_id).one_or_none()
    if not e:
        raise ValueError("expense_id not found")
    return e


def _normalize_spent_at(spent_at: Any) -> str:
    """
    Accept 'YYYY-MM-DD' and store as the same string.
    (This avoids DATE-vs-TEXT mismatch issues in your models.)
    """
    _require_non_empty(spent_at, "spent_at")
    s = str(spent_at).strip()
    try:
        date.fromisoformat(s)  # validate format
    except Exception:
        raise ValueError("spent_at must be ISO format YYYY-MM-DD")
    return s


# -------------------------
# Repo API (used by app.py)
# -------------------------

def create_expense_db(db: Session, payload: Dict[str, Any]) -> Dict[str, Any]:
    _require_non_empty(payload.get("user_id"), "user_id")

    if payload.get("amount") is None or float(payload["amount"]) <= 0:
        raise ValueError("amount must be > 0")

    _require_non_empty(payload.get("currency"), "currency")
    _require_non_empty(payload.get("category"), "category")
    _require_non_empty(payload.get("description"), "description")

    spent_at_norm = _normalize_spent_at(payload.get("spent_at"))

    e = Expense(
        expense_id=str(uuid4()),
        user_id=str(payload["user_id"]).strip(),
        amount=float(payload["amount"]),
        currency=str(payload["currency"]).strip(),
        category=str(payload["category"]).strip(),
        description=str(payload["description"]).strip(),
        spent_at=spent_at_norm,      # <-- store as string (safe with your current model)
        status="submitted",
        approved_by=None,
        rejected_by=None,
        rejection_reason=None,
    )

    db.add(e)
    db.commit()
    db.refresh(e)
    return _to_dict(e)


def list_expenses_by_user_id(db: Session, user_id: str) -> List[Dict[str, Any]]:
    _require_non_empty(user_id, "user_id")
    rows = db.query(Expense).filter(Expense.user_id == user_id).all()
    return [_to_dict(r) for r in rows]


def approve_expense_db(db: Session, expense_id: str, acted_by_user_id: str) -> Dict[str, Any]:
    _require_non_empty(expense_id, "expense_id")
    _require_non_empty(acted_by_user_id, "acted_by_user_id")

    e = _get_expense_or_raise(db, expense_id)

    if e.status != "submitted":
        raise ValueError("only submitted expenses can be approved or rejected")

    e.status = "approved"
    e.approved_by = acted_by_user_id
    e.rejected_by = None
    e.rejection_reason = None

    db.add(e)
    db.commit()
    db.refresh(e)
    return _to_dict(e)


def reject_expense_db(db: Session, expense_id: str, acted_by_user_id: str, reason: str) -> Dict[str, Any]:
    _require_non_empty(expense_id, "expense_id")
    _require_non_empty(acted_by_user_id, "acted_by_user_id")
    _require_non_empty(reason, "reason")

    e = _get_expense_or_raise(db, expense_id)

    if e.status != "submitted":
        raise ValueError("only submitted expenses can be approved or rejected")

    e.status = "rejected"
    e.rejected_by = acted_by_user_id
    e.rejection_reason = str(reason).strip()
    e.approved_by = None

    db.add(e)
    db.commit()
    db.refresh(e)
    return _to_dict(e)
