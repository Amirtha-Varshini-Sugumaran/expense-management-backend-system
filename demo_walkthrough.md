# Demo Walkthrough

This flow is designed for Swagger UI at `http://127.0.0.1:8000/docs`.

## 1. Start the system

```bash
docker compose up -d
python -m src.seed_demo --reset
python -m uvicorn src.app:app --reload
```

Use these demo headers:

| Person | X-User-Id | X-User-Role |
|---|---|---|
| Employee | `emp_001` | `employee` |
| Second employee | `emp_002` | `employee` |
| Manager | `mgr_001` | `manager` |
| Finance reviewer | `fin_001` | `finance` |

## 2. Employee submits an expense

`POST /expenses`

Headers:

```text
X-User-Id: emp_001
X-User-Role: employee
```

Body:

```json
{
  "amount": 36.4,
  "currency": "EUR",
  "category": "travel",
  "description": "Train ticket to client workshop",
  "expense_date": "2026-04-14",
  "receipt_name": "train-ticket.pdf"
}
```

Expected result: the expense is created with `status=submitted` and a first audit history entry.

## 3. Manager approves one expense

`POST /expenses/{expense_id}/approve`

Headers:

```text
X-User-Id: mgr_001
X-User-Role: manager
```

Body:

```json
{
  "manager_comment": "Within travel policy."
}
```

Expected result: the status changes to `approved`, `decided_by` is `mgr_001`, and history shows the approval.

## 4. Manager rejects one expense

`POST /expenses/{expense_id}/reject`

Headers:

```text
X-User-Id: mgr_001
X-User-Role: manager
```

Body:

```json
{
  "rejection_reason": "Receipt image is unreadable.",
  "manager_comment": "Please resubmit with a clearer receipt."
}
```

Expected result: the status changes to `rejected` and the rejection reason is stored.

## 5. Finance reviews filtered expenses

`GET /expenses?status=approved&limit=10&offset=0&sort=submitted_at_desc`

Headers:

```text
X-User-Id: fin_001
X-User-Role: finance
```

Expected result: finance can view expenses across employees with pagination metadata.

## 6. Show audit history

`GET /expenses/{expense_id}`

Use manager or finance headers to show the full audit history for the expense.
