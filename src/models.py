from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class Expense(Base):
    __tablename__ = "expenses"

    expense_id: Mapped[str] = mapped_column(String, primary_key=True)
    submitted_by: Mapped[str] = mapped_column(String, nullable=False, index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    manager_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    history: Mapped[list["ExpenseStatusHistory"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",
        order_by="ExpenseStatusHistory.acted_at",
    )


class ExpenseStatusHistory(Base):
    __tablename__ = "expense_status_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expense_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("expenses.expense_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    acted_by: Mapped[str] = mapped_column(String, nullable=False)
    acted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    expense: Mapped[Expense] = relationship(back_populates="history")
