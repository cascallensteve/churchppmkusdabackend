# Donation Account Funds Management

Admin endpoints to manage donation type accounts: add funds, record expenses, allocate funds, and manage adjustments.

**Base URL:** `/api/payments/`

---

## 1. Add Funds (Adjustment)

Add funds to a donation type account manually.

### Endpoint

- **URL:** `/api/payments/adjust/`
- **Method:** `POST`
- **Auth:** Admin user

### Payload

```json
{
    "donation_type": 1,
    "amount": 5000.00,
    "reason": "Bank deposit correction"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type` | integer | Yes | ID of the `DonationType` account |
| `amount` | decimal | Yes | Amount to add. Must be greater than zero |
| `reason` | string | Yes | Reason for the adjustment |

### Response

**201 Created**

```json
{
    "detail": "Funds adjusted successfully.",
    "adjustment": {
        "id": 1,
        "donation_type": 1,
        "amount": "5000.00",
        "reason": "Bank deposit correction",
        "created_by": 1,
        "created_by_email": "admin@example.com",
        "new_balance": "20000.00",
        "created_at": "2026-08-27T11:40:00Z"
    }
}
```

---

## 2. Adjustments (List, Edit, Delete)

Manage all fund adjustments for donation type accounts.

### 2.1 List Adjustments

- **URL:** `/api/payments/adjustments/`
- **Method:** `GET`
- **Auth:** Admin user

**200 OK**

```json
[
    {
        "id": 1,
        "donation_type": 1,
        "amount": "5000.00",
        "reason": "Bank deposit correction",
        "created_by": 1,
        "created_by_email": "admin@example.com",
        "new_balance": "20000.00",
        "created_at": "2026-08-27T11:40:00Z"
    }
]
```

### 2.2 Edit Adjustment

- **URL:** `/api/payments/adjustments/{id}/`
- **Method:** `PUT` or `PATCH`
- **Auth:** Admin user

**PUT Request**

```json
{
    "donation_type": 1,
    "amount": 6000.00,
    "reason": "Updated bank deposit"
}
```

**200 OK**

```json
{
    "id": 1,
    "donation_type": 1,
    "amount": "6000.00",
    "reason": "Updated bank deposit",
    "created_by": 1,
    "created_by_email": "admin@example.com",
    "new_balance": "21000.00",
    "created_at": "2026-08-27T11:40:00Z"
}
```

### 2.3 Delete Adjustment

- **URL:** `/api/payments/adjustments/{id}/`
- **Method:** `DELETE`
- **Auth:** Admin user

**204 No Content**

The donation type balance is recalculated automatically after deletion.

---

## 3. Record Spending (Expense)

Record an expense/spending against a donation type account.

### Endpoint

- **URL:** `/api/payments/spend/`
- **Method:** `POST`
- **Auth:** Admin user

### Payload

```json
{
    "donation_type": 1,
    "amount": 2500.00,
    "description": "Purchase of communion elements"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type` | integer | Yes | ID of the `DonationType` account to spend from |
| `amount` | decimal | Yes | Amount to spend. Must be greater than zero and not exceed current balance |
| `description` | string | Yes | Description of the expense |

### Response

**201 Created**

```json
{
    "detail": "Expense recorded successfully.",
    "expense": {
        "id": 1,
        "donation_type": 1,
        "amount": "2500.00",
        "description": "Purchase of communion elements",
        "created_by": 1,
        "created_by_email": "admin@example.com",
        "initial_balance": "15000.00",
        "remaining_balance": "12500.00",
        "created_at": "2026-08-26T17:16:00Z"
    }
}
```

---

## 4. Expenses (List, Edit, Delete)

Manage all expenses for donation type accounts.

### 4.1 List Expenses

- **URL:** `/api/payments/expenses/`
- **Method:** `GET`
- **Auth:** Admin user

**200 OK**

```json
[
    {
        "id": 1,
        "donation_type": 1,
        "amount": "2500.00",
        "description": "Purchase of communion elements",
        "created_by": 1,
        "created_by_email": "admin@example.com",
        "initial_balance": "15000.00",
        "remaining_balance": "12500.00",
        "created_at": "2026-08-26T17:16:00Z"
    }
]
```

### 4.2 Edit Expense

- **URL:** `/api/payments/expenses/{id}/`
- **Method:** `PUT` or `PATCH`
- **Auth:** Admin user

**PUT Request**

```json
{
    "donation_type": 1,
    "amount": 3000.00,
    "description": "Updated communion elements purchase"
}
```

**200 OK**

```json
{
    "id": 1,
    "donation_type": 1,
    "amount": "3000.00",
    "description": "Updated communion elements purchase",
    "created_by": 1,
    "created_by_email": "admin@example.com",
    "initial_balance": "15000.00",
    "remaining_balance": "12000.00",
    "created_at": "2026-08-26T17:16:00Z"
}
```

### 4.3 Delete Expense

- **URL:** `/api/payments/expenses/{id}/`
- **Method:** `DELETE`
- **Auth:** Admin user

**204 No Content**

The donation type balance is recalculated automatically after deletion.

---

## 5. Allocate Funds

Allocate funds from a donation type account to a recipient.

### Endpoint

- **URL:** `/api/payments/allocate/`
- **Method:** `POST`
- **Auth:** Admin user

### Payload

```json
{
    "donation_type": 1,
    "amount": 5000.00,
    "recipient_name": "Grace Ministry",
    "recipient_email": "grace@example.com",
    "purpose": "Youth program funding"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type` | integer | Yes | ID of the `DonationType` account to allocate from |
| `amount` | decimal | Yes | Amount to allocate. Must be greater than zero and not exceed current balance |
| `recipient_name` | string | Yes | Name of the recipient |
| `recipient_email` | string | No | Email of the recipient |
| `purpose` | string | Yes | Purpose of the allocation |

### Response

**201 Created**

```json
{
    "detail": "Funds allocated successfully.",
    "allocation": {
        "id": 1,
        "donation_type": 1,
        "amount": "5000.00",
        "allocated_by": 1,
        "allocated_by_email": "admin@example.com",
        "recipient_name": "Grace Ministry",
        "recipient_email": "grace@example.com",
        "purpose": "Youth program funding",
        "remaining_balance": "10000.00",
        "created_at": "2026-08-26T18:00:00Z"
    }
}
```

---

## 6. Allocations (List, Edit, Delete)

Manage all fund allocations for donation type accounts.

### 6.1 List Allocations

- **URL:** `/api/payments/allocations/`
- **Method:** `GET`
- **Auth:** Admin user

**200 OK**

```json
[
    {
        "id": 1,
        "donation_type": 1,
        "amount": "5000.00",
        "allocated_by": 1,
        "allocated_by_email": "admin@example.com",
        "recipient_name": "Grace Ministry",
        "recipient_email": "grace@example.com",
        "purpose": "Youth program funding",
        "remaining_balance": "10000.00",
        "created_at": "2026-08-26T18:00:00Z"
    }
]
```

### 6.2 Edit Allocation

- **URL:** `/api/payments/allocations/{id}/`
- **Method:** `PUT` or `PATCH`
- **Auth:** Admin user

**PUT Request**

```json
{
    "donation_type": 1,
    "amount": 6000.00,
    "recipient_name": "Grace Ministry",
    "recipient_email": "grace@example.com",
    "purpose": "Updated youth program funding"
}
```

**200 OK**

```json
{
    "id": 1,
    "donation_type": 1,
    "amount": "6000.00",
    "allocated_by": 1,
    "allocated_by_email": "admin@example.com",
    "recipient_name": "Grace Ministry",
    "recipient_email": "grace@example.com",
    "purpose": "Updated youth program funding",
    "remaining_balance": "9000.00",
    "created_at": "2026-08-26T18:00:00Z"
}
```

### 6.3 Delete Allocation

- **URL:** `/api/payments/allocations/{id}/`
- **Method:** `DELETE`
- **Auth:** Admin user

**204 No Content**

The donation type balance is recalculated automatically after deletion.

---

## Error Responses

**400 Bad Request - Insufficient funds:**

```json
{
    "detail": "Insufficient funds in Tithe. Current balance: 1000.00, requested: 2500.00"
}
```

**400 Bad Request - Amount must be greater than zero:**

```json
{
    "amount": ["Amount must be greater than zero."]
}
```

**401 Unauthorized:**

```json
{
    "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**

```json
{
    "detail": "You do not have permission to perform this action."
}
```

**404 Not Found:**

```json
{
    "detail": "Not found."
}
```

---

## Balance Calculation

The donation type balance is calculated automatically as:

```
Balance = Total Successful Transactions - Total Allocations - Total Expenses + Total Adjustments
```

All endpoints recalculate the balance after any create, update, or delete operation.

---

## Notes

- All endpoints require admin authentication
- Balance is always recalculated automatically after any operation
- Deleting an adjustment/expense/allocation restores the balance
- Editing an adjustment/expense/allocation recalculates the balance with the new amount
- Use adjustments for adding funds (bank deposits, corrections)
- Use expenses for spending funds (purchases, bills)
- Use allocations for assigning funds to specific recipients/purposes
