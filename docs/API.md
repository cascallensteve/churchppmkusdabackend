# Payments API Documentation

Base URL: `/api/payments/`

All endpoints are prefixed with `/api/payments/`.

---

## 1. Initiate Payment (STK Push)

Initiates an M-Pesa STK Push payment for a specific donation type.

### Endpoint

- **URL:** `/api/payments/initiate/`
- **Method:** `POST`
- **Auth:** Public

### Payload

```json
{
    "donation_type_id": 4,
    "donor_name": "John Doe",
    "donor_email": "john@example.com",
    "phone_number": "254712665257",
    "amount": 1.00 
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type_id` | integer | Yes | ID of the `DonationType` to pay for |
| `phone_number` | string | Yes | M-Pesa registered phone number |
| `amount` | decimal | Yes | Amount to donate |

### Responses

**200 OK**

```json
{
    "message": "Payment initiated successfully. Please check your phone.",
    "checkout_request_id": "ws_CO_123456789",
    "transaction": {
        "id": 1,
        "donation_type": 1,
        "donation_type_name": "Tithe",
        "user": null,
        "user_email": null,
        "phone_number": "254712345678",
        "amount": "100.00",
        "status": "PENDING",
        "mpesa_receipt": null,
        "merchant_request_id": "12345-1",
        "checkout_request_id": "ws_CO_123456789",
        "transaction_desc": "Payment for Tithe",
        "created_at": "2026-08-25T19:00:00Z",
        "updated_at": "2026-08-25T19:00:00Z"
    }
}
```

**400 Bad Request**

```json
{
    "detail": "donation_type_id, phone_number, and amount are required."
}
```

**404 Not Found**

```json
{
    "detail": "Donation type not found."
}
```

**500 Internal Server Error**

```json
{
    "detail": "Failed to create transaction: <error message>"
}
```

or

```json
{
    "detail": "Error connecting to M-Pesa: <error message>"
}
```

---

## 2. M-Pesa Validation (Webhook)

M-Pesa validation endpoint. Returns accepted for all requests.

### Endpoint

- **URL:** `/api/payments/validation/`
- **Method:** `POST`
- **Auth:** Public

### Payload


M-Pesa sends a payload here for validation before initiating STK Push.

### Responses

**200 OK**

```json
{
    "ResultCode": 0,
    "ResultDesc": "Accepted"
}
```

---

## 3. M-Pesa Callback (Webhook)

M-Pesa callback endpoint. Updates the `Transaction` status based on the STK Push result.

### Endpoint

- **URL:** `/api/payments/callback/`
- **Method:** `POST`
- **Auth:** Public

### Payload

```json
{
    "Body": {
        "stkCallback": {
            "CheckoutRequestID": "ws_CO_123456789",
            "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {
                "Item": [
                    { "Name": "MpesaReceiptNumber", "Value": "ABC123" },
                    { "Name": "Amount", "Value": 100.00 }
                ]
            }
        }
    }
}
```

| Field | Type | Description |
|---|---|---|
| `Body.stkCallback.CheckoutRequestID` | string | The checkout request ID to match the transaction |
| `Body.stkCallback.ResultCode` | integer | `0` for success, non-zero for failure |
| `Body.stkCallback.ResultDesc` | string | Description of the result |
| `Body.stkCallback.CallbackMetadata.Item` | array | List of metadata items |

### Responses

**200 OK**

```json
{
    "ResultCode": 0,
    "ResultDesc": "Accepted"
}
```

---

## 4. Payment Status

Check the status of a payment by `checkout_request_id`.

### Endpoint

- **URL:** `/api/payments/status/`
- **Method:** `GET`
- **Auth:** Public

### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `checkout_request_id` | string | Yes | The `checkout_request_id` returned from initiate |

Example: `/api/payments/status/?checkout_request_id=ws_CO_123456789`

### Responses

**200 OK**

```json
{
    "id": 1,
    "donation_type": 1,
    "donation_type_name": "Tithe",
    "user": null,
    "user_email": null,
    "phone_number": "254712345678",
    "amount": "100.00",
    "status": "SUCCESS",
    "mpesa_receipt": "ABC123",
    "merchant_request_id": "12345-1",
    "checkout_request_id": "ws_CO_123456789",
    "transaction_desc": "Payment for Tithe",
    "created_at": "2026-08-25T19:00:00Z",
    "updated_at": "2026-08-25T19:00:01Z"
}
```

**400 Bad Request**

```json
{
    "detail": "checkout_request_id is required."
}
```

**404 Not Found**

```json
{
    "detail": "Transaction not found."
}
```

---

## 5. List Transactions (Admin)

List all donation transactions. Admin-only.

### Endpoint

- **URL:** `/api/payments/transactions/`
- **Method:** `GET`
- **Auth:** Admin user

### Payload

None. This is a GET endpoint.

### Responses

**200 OK**

```json
[
    {
        "id": 1,
        "donation_type": 1,
        "donation_type_name": "Tithe",
        "user": null,
        "user_email": null,
        "phone_number": "254712345678",
        "amount": "100.00",
        "status": "SUCCESS",
        "mpesa_receipt": "ABC123",
        "merchant_request_id": "12345-1",
        "checkout_request_id": "ws_CO_123456789",
        "transaction_desc": "Payment for Tithe",
        "created_at": "2026-08-25T19:00:00Z",
        "updated_at": "2026-08-25T19:00:01Z"
    }
]
```

**401 Unauthorized**

```json
{
    "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**

```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

## 6. Transaction Detail (Admin)

Retrieve a single transaction by ID. Admin-only.

### Endpoint

- **URL:** `/api/payments/transactions/{id}/`
- **Method:** `GET`
- **Auth:** Admin user

### Payload

None. This is a GET endpoint.

### Responses

**200 OK**

```json
{
    "id": 1,
    "donation_type": 1,
    "donation_type_name": "Tithe",
    "user": null,
    "user_email": null,
    "phone_number": "254712345678",
    "amount": "100.00",
    "status": "SUCCESS",
    "mpesa_receipt": "ABC123",
    "merchant_request_id": "12345-1",
    "checkout_request_id": "ws_CO_123456789",
    "transaction_desc": "Payment for Tithe",
    "created_at": "2026-08-25T19:00:00Z",
    "updated_at": "2026-08-25T19:00:01Z"
}
```

**401 Unauthorized**

```json
{
    "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**

```json
{
    "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**

```json
{
    "detail": "Not found."
}
```

---

## 7. Donation Type Statistics (Admin)

Get aggregated statistics for all donation type accounts. Admin-only.

### Endpoint

- **URL:** `/api/payments/stats/donation-types/`
- **Method:** `GET`
- **Auth:** Admin user

### Payload

None. This is a GET endpoint.

### Responses

**200 OK**

```json
[
    {
        "id": 1,
        "name": "Tithe",
        "description": "General tithe donation",
        "current_balance": 15000.00,
        "total_transactions": 25,
        "successful_transactions": 22,
        "pending_transactions": 2,
        "failed_transactions": 1,
        "cancelled_transactions": 0,
        "total_amount_received": 20000.00,
        "cash_amount": 5000.00,
        "mpesa_amount": 15000.00,
        "total_allocated": 5000.00
    },

    {
        "id": 2,
        "name": "Offering",
        "description": "Sunday offering",
        "current_balance": 8500.00,
        "total_transactions": 18,
        "successful_transactions": 16,
        "pending_transactions": 1,
        "failed_transactions": 1,
        "cancelled_transactions": 0,
        "total_amount_received": 12000.00,
        "cash_amount": 3000.00,
        "mpesa_amount": 9000.00,
        "total_allocated": 3500.00
    }
]
```

| Field | Type | Description |
|---|---|---|
| `id` | integer | Donation type ID |
| `name` | string | Donation type name |
| `description` | string | Donation type description |
| `current_balance` | decimal | Current available balance |
| `total_transactions` | integer | Total number of transactions |
| `successful_transactions` | integer | Number of successful transactions |
| `pending_transactions` | integer | Number of pending transactions |
| `failed_transactions` | integer | Number of failed transactions |
| `cancelled_transactions` | integer | Number of cancelled transactions |
| `total_amount_received` | decimal | Total amount from successful transactions |
| `cash_amount` | decimal | Total cash amount received |
| `mpesa_amount` | decimal | Total M-Pesa amount received |
| `total_allocated` | decimal | Total amount allocated from this account |

**401 Unauthorized**

```json
{
    "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**

```json
{
    "detail": "You do not have permission to perform this action."
}
```


---

## 9. Record Spending (Admin)

Record an expense/spending against a donation type account and return the remaining balance. Admin-only.

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

