from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session, selectinload

from src.models import Expense, ExpenseStatusHistory


ALLOWED_CATEGORIES = {
    "travel",
    "meals",
    "office",
    "software",
    "training",
    "client",
    "other",
}
ALLOWED_CURRENCIES = {"EUR", "GBP", "USD", "INR"}
FINAL_STATUSES = {"approved", "rejected"}


@dataclass
class ExpenseServiceError(Exception):
    message: str
    status_code: int = 400

    def __str__(self) -> str:
        return self.message


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _require_non_empty(value: Any, field: str) -> str:
    if value is None or str(value).strip() == "":
        raise ExpenseServiceError(f"{field} is required")
    return str(value).strip()


def _optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    clean = str(value).strip()
    return clean or None


def _amount(value: Any) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ExpenseServiceError("amount must be a positive number")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ExpenseServiceError("amount must be a positive number")
    if amount <= 0:
        raise ExpenseServiceError("amount must be greater than zero")
    return amount.quantize(Decimal("0.01"))


def _currency(value: Any) -> str:
    currency = _require_non_empty(value, "currency").upper()
    if currency not in ALLOWED_CURRENCIES:
        allowed = ", ".join(sorted(ALLOWED_CURRENCIES))
        raise ExpenseServiceError(f"currency must be one of: {allowed}")
    return currency


def _category(value: Any) -> str:
    category = _require_non_empty(value, "category").lower()
    if category not in ALLOWED_CATEGORIES:
        allowed = ", ".join(sorted(ALLOWED_CATEGORIES))
        raise ExpenseServiceError(f"category must be one of: {allowed}")
    return category


def _expense_date(value: Any) -> date:
    raw = _require_non_empty(value, "expense_date")
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        raise ExpenseServiceError("expense_date must use ISO format YYYY-MM-DD")
    if parsed > date.today():
        raise ExpenseServiceError("expense_date cannot be in the future")
    return parsed


def _get_expense_or_raise(db: Session, expense_id: str) -> Expense:
    expense_id = _require_non_empty(expense_id, "expense_id")
    expense = (
        db.query(Expense)
        .options(selectinload(Expense.history))
        .filter(Expense.expense_id == expense_id)
        .one_or_none()
    )
    if not expense:
        raise ExpenseServiceError("expense not found", status_code=404)
    return expense


def _history_to_dict(row: ExpenseStatusHistory) -> Dict[str, Any]:
    return {
        "history_id": row.history_id,
        "from_status": row.from_status,
        "to_status": row.to_status,
        "action": row.action,
        "acted_by": row.acted_by,
        "acted_at": row.acted_at.isoformat(),
        "comment": row.comment,
    }


def expense_to_dict(expense: Expense, include_history: bool = False) -> Dict[str, Any]:
    data = {
        "expense_id": expense.expense_id,
        "submitted_by": expense.submitted_by,
        "amount": float(expense.amount),
        "currency": expense.currency,
        "category": expense.category,
        "description": expense.description,
        "expense_date": expense.expense_date.isoformat(),
        "receipt_name": expense.receipt_name,
        "receipt_url": expense.receipt_url,
        "status": expense.status,
        "submitted_at": expense.submitted_at.isoformat(),
        "decided_at": expense.decided_at.isoformat() if expense.decided_at else None,
        "decided_by": expense.decided_by,
        "manager_comment": expense.manager_comment,
        "rejection_reason": expense.rejection_reason,
    }
    if include_history:
        data["history"] = [_history_to_dict(row) for row in expense.history]
    return data


def _record_history(
    db: Session,
    expense: Expense,
    from_status: Optional[str],
    to_status: str,
    action: str,
    acted_by: str,
    comment: Optional[str] = None,
) -> None:
    db.add(
        ExpenseStatusHistory(
            expense_id=expense.expense_id,
            from_status=from_status,
            to_status=to_status,
            action=action,
            acted_by=acted_by,
            acted_at=_utcnow(),
            comment=comment,
        )
    )


def create_expense_db(db: Session, payload: Dict[str, Any], submitted_by: Optional[str] = None) -> Dict[str, Any]:
    employee_id = submitted_by or payload.get("submitted_by") or payload.get("user_id")
    employee_id = _require_non_empty(employee_id, "submitted_by")

    expense = Expense(
        expense_id=str(uuid4()),
        submitted_by=employee_id,
        amount=_amount(payload.get("amount")),
        currency=_currency(payload.get("currency")),
        category=_category(payload.get("category")),
        description=_require_non_empty(payload.get("description"), "description"),
        expense_date=_expense_date(payload.get("expense_date") or payload.get("spent_at")),
        receipt_name=_optional_text(payload.get("receipt_name")),
        receipt_url=_optional_text(payload.get("receipt_url")),
        status="submitted",
        submitted_at=_utcnow(),
        decided_at=None,
        decided_by=None,
        manager_comment=None,
        rejection_reason=None,
    )

    db.add(expense)
    _record_history(
        db,
        expense,
        from_status=None,
        to_status="submitted",
        action="submitted",
        acted_by=employee_id,
        comment="Expense submitted",
    )
    db.commit()
    db.refresh(expense)
    return expense_to_dict(expense, include_history=True)


def list_expenses_db(
    db: Session,
    *,
    submitted_by: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
    sort: str = "submitted_at_desc",
) -> Dict[str, Any]:
    query = db.query(Expense)

    if submitted_by:
        query = query.filter(Expense.submitted_by == submitted_by.strip())
    if status:
        status = status.strip().lower()
        if status not in {"submitted", "approved", "rejected"}:
            raise ExpenseServiceError("status must be submitted, approved, or rejected")
        query = query.filter(Expense.status == status)
    if category:
        query = query.filter(Expense.category == _category(category))

    total = query.with_entities(func.count()).scalar() or 0

    sort_map = {
        "submitted_at_desc": desc(Expense.submitted_at),
        "submitted_at_asc": asc(Expense.submitted_at),
        "amount_desc": desc(Expense.amount),
        "amount_asc": asc(Expense.amount),
        "expense_date_desc": desc(Expense.expense_date),
        "expense_date_asc": asc(Expense.expense_date),
    }
    if sort not in sort_map:
        raise ExpenseServiceError("sort must be one of: " + ", ".join(sort_map.keys()))

    rows = query.order_by(sort_map[sort]).offset(offset).limit(limit).all()
    return {
        "items": [expense_to_dict(row) for row in rows],
        "total": int(total),
        "limit": limit,
        "offset": offset,
    }


def get_expense_db(db: Session, expense_id: str) -> Dict[str, Any]:
    return expense_to_dict(_get_expense_or_raise(db, expense_id), include_history=True)


def _ensure_reviewer_can_act(expense: Expense, acted_by_user_id: str, role: str) -> str:
    actor = _require_non_empty(acted_by_user_id, "acted_by_user_id")
    if role not in {"manager", "finance"}:
        raise ExpenseServiceError("only manager or finance users can review expenses", status_code=403)
    if expense.submitted_by == actor:
        raise ExpenseServiceError("users cannot approve or reject their own expenses", status_code=403)
    if expense.status in FINAL_STATUSES:
        raise ExpenseServiceError("approved or rejected expenses cannot be reviewed again", status_code=409)
    if expense.status != "submitted":
        raise ExpenseServiceError("only submitted expenses can be approved or rejected", status_code=409)
    return actor


def approve_expense_db(
    db: Session,
    *,
    expense_id: str,
    acted_by_user_id: str,
    role: str,
    manager_comment: Optional[str] = None,
) -> Dict[str, Any]:
    expense = _get_expense_or_raise(db, expense_id)
    actor = _ensure_reviewer_can_act(expense, acted_by_user_id, role)

    previous_status = expense.status
    expense.status = "approved"
    expense.decided_at = _utcnow()
    expense.decided_by = actor
    expense.manager_comment = _optional_text(manager_comment)
    expense.rejection_reason = None
    _record_history(db, expense, previous_status, "approved", "approved", actor, expense.manager_comment)

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense_to_dict(expense, include_history=True)


def reject_expense_db(
    db: Session,
    *,
    expense_id: str,
    acted_by_user_id: str,
    role: str,
    reason: str,
    manager_comment: Optional[str] = None,
) -> Dict[str, Any]:
    reason = _require_non_empty(reason, "rejection_reason")
    expense = _get_expense_or_raise(db, expense_id)
    actor = _ensure_reviewer_can_act(expense, acted_by_user_id, role)

    previous_status = expense.status
    expense.status = "rejected"
    expense.decided_at = _utcnow()
    expense.decided_by = actor
    expense.manager_comment = _optional_text(manager_comment)
    expense.rejection_reason = reason
    _record_history(db, expense, previous_status, "rejected", "rejected", actor, reason)

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense_to_dict(expense, include_history=True)
