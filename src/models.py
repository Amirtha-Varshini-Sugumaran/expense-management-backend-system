from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, Numeric

from src.db import Base


class Expense(Base):
    __tablename__ = "expenses"

    expense_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    spent_at: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)  # submitted/approved/rejected
    approved_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)