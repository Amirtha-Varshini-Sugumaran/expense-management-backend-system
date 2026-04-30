from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.db import SessionLocal, DATABASE_URL

# IMPORTANT:
# These functions MUST exist in src/repositories/expense_repo.py
from src.repositories.expense_repo import (
    create_expense_db,
    list_expenses_by_user_id,
    approve_expense_db,
    reject_expense_db,
)

app = FastAPI(
    title="Expense Management Backend System (EMBS)",
    version="1.0.0",
    description="Internal API for managing employee expenses",
    debug=True,   # <-- added
)


# -----------------------
# Pydantic models
# -----------------------

class ExpenseCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=1, examples=["user_1"])
    amount: float = Field(..., gt=0, examples=[100.0])
    currency: str = Field(..., min_length=1, examples=["EUR"])
    category: str = Field(..., min_length=1, examples=["travel"])
    description: str = Field(..., min_length=1, examples=["Taxi"])
    spent_at: str = Field(..., min_length=1, examples=["2026-01-20"])


class ApproveRequest(BaseModel):
    acted_by_user_id: str = Field(..., min_length=1, examples=["manager_1"])


class RejectRequest(BaseModel):
    acted_by_user_id: str = Field(..., min_length=1, examples=["manager_1"])
    reason: str = Field(..., min_length=1, examples=["Receipt missing"])


# -----------------------
# Helpers
# -----------------------

def _bad_request(e: Exception) -> None:
    raise HTTPException(status_code=400, detail=str(e))


def _session():
    return SessionLocal()


# -----------------------
# Routes
# -----------------------

@app.get("/health")
def health():
    s = _session()
    try:
        total = s.execute(text("select count(*) from expenses")).scalar()
        return {
            "status": "ok",
            "database_url": DATABASE_URL,
            "expenses_total": int(total or 0),
        }
    finally:
        s.close()


@app.post("/expenses")
def create_expense(req: ExpenseCreateRequest):
    s = _session()
    try:
        return create_expense_db(s, req.model_dump())
    except ValueError as e:
        _bad_request(e)
    finally:
        s.close()


@app.get("/expenses")
def list_expenses(
    user_id: str = Query(..., min_length=1, description="User ID"),
):
    s = _session()
    try:
        return list_expenses_by_user_id(s, user_id=user_id)
    except ValueError as e:
        _bad_request(e)
    finally:
        s.close()


@app.post("/expenses/{expense_id}/approve")
def approve_expense(
    expense_id: str = Path(..., min_length=1),
    req: ApproveRequest = ...,
):
    s = _session()
    try:
        return approve_expense_db(s, expense_id=expense_id, acted_by_user_id=req.acted_by_user_id)
    except ValueError as e:
        _bad_request(e)
    finally:
        s.close()


@app.post("/expenses/{expense_id}/reject")
def reject_expense(
    expense_id: str = Path(..., min_length=1),
    req: RejectRequest = ...,
):
    s = _session()
    try:
        return reject_expense_db(
            s,
            expense_id=expense_id,
            acted_by_user_id=req.acted_by_user_id,
            reason=req.reason,
        )
    except ValueError as e:
        _bad_request(e)
    finally:
        s.close()
