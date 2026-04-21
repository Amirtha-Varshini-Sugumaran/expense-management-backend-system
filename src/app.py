from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query
from pydantic import BaseModel, Field, HttpUrl, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import DATABASE_URL, SessionLocal
from src.repositories.expense_repo import (
    ALLOWED_CATEGORIES,
    ExpenseServiceError,
    approve_expense_db,
    create_expense_db,
    get_expense_db,
    list_expenses_db,
    reject_expense_db,
)


app = FastAPI(
    title="Expense Management Backend API",
    version="2.0.0",
    description=(
        "A demo-ready expense approval backend with role-aware review actions, "
        "business validation, filtering, pagination, and audit history."
    ),
)


Role = Literal["employee", "manager", "finance"]
ExpenseStatus = Literal["submitted", "approved", "rejected"]


class ErrorResponse(BaseModel):
    detail: str


class CurrentUser(BaseModel):
    user_id: str
    role: Role


class ExpenseCreateRequest(BaseModel):
    submitted_by: Optional[str] = Field(
        None,
        description="Employee submitting the expense. Defaults to X-User-Id when omitted.",
        examples=["emp_001"],
    )
    amount: float = Field(..., gt=0, examples=[48.75])
    currency: str = Field(..., min_length=3, max_length=3, examples=["EUR"])
    category: str = Field(..., examples=["travel"])
    description: str = Field(..., min_length=3, examples=["Taxi from airport to client office"])
    expense_date: date = Field(..., examples=["2026-04-15"])
    receipt_name: Optional[str] = Field(None, examples=["taxi-receipt.pdf"])
    receipt_url: Optional[HttpUrl] = Field(None, examples=["https://example.com/receipts/taxi.pdf"])

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper().strip()

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.lower().strip()


class ReviewRequest(BaseModel):
    manager_comment: Optional[str] = Field(None, examples=["Approved for the Dublin client visit"])


class RejectRequest(ReviewRequest):
    rejection_reason: str = Field(..., min_length=3, examples=["Receipt is missing"])


class ExpenseHistoryResponse(BaseModel):
    history_id: int
    from_status: Optional[str]
    to_status: ExpenseStatus
    action: str
    acted_by: str
    acted_at: datetime
    comment: Optional[str]


class ExpenseResponse(BaseModel):
    expense_id: str
    submitted_by: str
    amount: float
    currency: str
    category: str
    description: str
    expense_date: date
    receipt_name: Optional[str]
    receipt_url: Optional[str]
    status: ExpenseStatus
    submitted_at: datetime
    decided_at: Optional[datetime]
    decided_by: Optional[str]
    manager_comment: Optional[str]
    rejection_reason: Optional[str]
    history: Optional[List[ExpenseHistoryResponse]] = None


class ExpenseListResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    limit: int
    offset: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    x_user_id: str = Header("emp_001", alias="X-User-Id"),
    x_user_role: Role = Header("employee", alias="X-User-Role"),
) -> CurrentUser:
    user_id = x_user_id.strip()
    if not user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header is required")
    return CurrentUser(user_id=user_id, role=x_user_role)


def _handle_service_error(error: ExpenseServiceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.message)


@app.get(
    "/health",
    summary="Check API and database health",
    responses={503: {"model": ErrorResponse}},
)
def health(db: Session = Depends(get_db)):
    try:
        total = db.execute(text("select count(*) from expenses")).scalar()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}")
    return {
        "status": "ok",
        "database": "connected",
        "database_url": DATABASE_URL,
        "expenses_total": int(total or 0),
    }


@app.get("/demo/users", summary="Show demo identities for Swagger testing")
def demo_users():
    return {
        "employees": ["emp_001", "emp_002"],
        "managers": ["mgr_001"],
        "finance": ["fin_001"],
        "header_usage": "Set X-User-Id and X-User-Role in Swagger or curl requests.",
    }


@app.post(
    "/expenses",
    response_model=ExpenseResponse,
    status_code=201,
    summary="Submit a new expense",
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def create_expense(
    req: ExpenseCreateRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if user.role != "employee":
        raise HTTPException(status_code=403, detail="only employees can submit expenses")
    submitted_by = req.submitted_by or user.user_id
    if submitted_by != user.user_id:
        raise HTTPException(status_code=403, detail="employees can only submit their own expenses")
    try:
        return create_expense_db(db, req.model_dump(mode="json"), submitted_by=user.user_id)
    except ExpenseServiceError as error:
        _handle_service_error(error)


@app.get(
    "/expenses",
    response_model=ExpenseListResponse,
    summary="List expenses with filtering, pagination, and sorting",
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def list_expenses(
    submitted_by: Optional[str] = Query(None, description="Employee ID to filter by"),
    status: Optional[ExpenseStatus] = Query(None),
    category: Optional[str] = Query(None, description=f"One of: {', '.join(sorted(ALLOWED_CATEGORIES))}"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query(
        "submitted_at_desc",
        description="submitted_at_desc, submitted_at_asc, amount_desc, amount_asc, expense_date_desc, expense_date_asc",
    ),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if user.role == "employee":
        if submitted_by and submitted_by != user.user_id:
            raise HTTPException(status_code=403, detail="employees can only list their own expenses")
        submitted_by = user.user_id

    try:
        return list_expenses_db(
            db,
            submitted_by=submitted_by,
            status=status,
            category=category,
            limit=limit,
            offset=offset,
            sort=sort,
        )
    except ExpenseServiceError as error:
        _handle_service_error(error)


@app.get(
    "/expenses/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get one expense with audit history",
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def get_expense(
    expense_id: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        expense = get_expense_db(db, expense_id)
    except ExpenseServiceError as error:
        _handle_service_error(error)
    if user.role == "employee" and expense["submitted_by"] != user.user_id:
        raise HTTPException(status_code=403, detail="employees can only view their own expenses")
    return expense


@app.post(
    "/expenses/{expense_id}/approve",
    response_model=ExpenseResponse,
    summary="Approve a submitted expense",
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def approve_expense(
    req: ReviewRequest,
    expense_id: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        return approve_expense_db(
            db,
            expense_id=expense_id,
            acted_by_user_id=user.user_id,
            role=user.role,
            manager_comment=req.manager_comment,
        )
    except ExpenseServiceError as error:
        _handle_service_error(error)


@app.post(
    "/expenses/{expense_id}/reject",
    response_model=ExpenseResponse,
    summary="Reject a submitted expense with a reason",
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def reject_expense(
    req: RejectRequest,
    expense_id: str = Path(..., min_length=1),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        return reject_expense_db(
            db,
            expense_id=expense_id,
            acted_by_user_id=user.user_id,
            role=user.role,
            reason=req.rejection_reason,
            manager_comment=req.manager_comment,
        )
    except ExpenseServiceError as error:
        _handle_service_error(error)
