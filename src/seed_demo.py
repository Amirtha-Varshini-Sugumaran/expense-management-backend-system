from __future__ import annotations

import argparse

from src import models  # noqa: F401
from src.db import Base, SessionLocal, engine
from src.repositories.expense_repo import approve_expense_db, create_expense_db, reject_expense_db


DEMO_EXPENSES = [
    {
        "submitted_by": "emp_001",
        "amount": 42.80,
        "currency": "EUR",
        "category": "travel",
        "description": "Taxi from Dublin Airport to client office",
        "expense_date": "2026-04-10",
        "receipt_name": "airport-taxi.pdf",
    },
    {
        "submitted_by": "emp_001",
        "amount": 18.50,
        "currency": "EUR",
        "category": "meals",
        "description": "Lunch during implementation workshop",
        "expense_date": "2026-04-12",
        "receipt_name": "workshop-lunch.jpg",
    },
    {
        "submitted_by": "emp_002",
        "amount": 129.99,
        "currency": "EUR",
        "category": "software",
        "description": "Annual diagramming tool subscription",
        "expense_date": "2026-04-08",
        "receipt_name": "software-invoice.pdf",
    },
]


def seed(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(models.Expense).count()
        if existing:
            print(f"Demo seed skipped: {existing} expenses already exist. Use --reset to rebuild demo data.")
            return

        submitted = [create_expense_db(db, payload) for payload in DEMO_EXPENSES]
        approve_expense_db(
            db,
            expense_id=submitted[0]["expense_id"],
            acted_by_user_id="mgr_001",
            role="manager",
            manager_comment="Client travel is within policy.",
        )
        reject_expense_db(
            db,
            expense_id=submitted[1]["expense_id"],
            acted_by_user_id="mgr_001",
            role="manager",
            reason="Receipt image is unreadable.",
            manager_comment="Please resubmit with a clearer receipt.",
        )

        print("Demo data created")
        print("Employee: emp_001 / role employee")
        print("Manager:  mgr_001 / role manager")
        print("Finance:  fin_001 / role finance")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo expense data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate demo tables before seeding")
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
