from src.core.expense import approve_expense, create_expense, list_expenses_for_user, reject_expense


def main():
    store = []

    taxi = create_expense(
        store,
        {
            "user_id": "emp_001",
            "amount": 42.80,
            "currency": "EUR",
            "category": "travel",
            "description": "Taxi from Dublin Airport to client office",
            "expense_date": "2026-04-10",
            "receipt_name": "airport-taxi.pdf",
        },
    )

    lunch = create_expense(
        store,
        {
            "user_id": "emp_001",
            "amount": 18.50,
            "currency": "EUR",
            "category": "meals",
            "description": "Lunch during implementation workshop",
            "expense_date": "2026-04-12",
            "receipt_name": "workshop-lunch.jpg",
        },
    )

    print("Submitted expenses:")
    print(list_expenses_for_user(store, "emp_001"))

    print("\nManager approves the taxi:")
    print(approve_expense(store, taxi["expense_id"], "mgr_001"))

    print("\nManager rejects the lunch:")
    print(reject_expense(store, lunch["expense_id"], "mgr_001", "Receipt image is unreadable"))


if __name__ == "__main__":
    main()
