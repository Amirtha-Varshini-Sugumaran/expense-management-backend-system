from core.expense import (
    create_expense,
    list_expenses_for_user,
    approve_expense,
    reject_expense,
)


def main():
    store = []

    expense1 = create_expense(
        store,
        {
            "user_id": "user_1",
            "amount": 100,
            "currency": "EUR",
            "category": "travel",
            "description": "Taxi to client meeting",
            "spent_at": "2026-01-20",
        },
    )

    expense2 = create_expense(
        store,
        {
            "user_id": "user_2",
            "amount": 50,
            "currency": "EUR",
            "category": "food",
            "description": "Lunch with client",
            "spent_at": "2026-01-21",
        },
    )

    print("Created expenses:")
    print(expense1)
    print(expense2)

    print("\nAll expenses in store:")
    print(store)

    print("\nExpenses for user_1:")
    print(list_expenses_for_user(store, "user_1"))

    print("\nExpenses for user_2:")
    print(list_expenses_for_user(store, "user_2"))

    print("\nExpenses for user_3 (none expected):")
    print(list_expenses_for_user(store, "user_3"))

    # ---- Step 7 tests (must be inside main) ----
    id1 = expense1["expense_id"]
    id2 = expense2["expense_id"]

    print("\nApprove expense1 by manager_1:")
    print(approve_expense(store, id1, "manager_1"))

    print("\nTry approving same expense again (should fail):")
    try:
        print(approve_expense(store, id1, "manager_1"))
    except ValueError as e:
        print("Expected error:", e)

    print("\nReject expense2 by manager_1:")
    print(reject_expense(store, id2, "manager_1", "Receipt missing"))


if __name__ == "__main__":
    main()
