# Donation API Documentation

Base URL: `/api/donation/`

All endpoints are prefixed with `/api/donation/`.

---

## 1. List Donation Types (Public)

List all available donation types.

### Endpoint

- **URL:** `/api/donation/public/`
- **Method:** `GET`
- **Auth:** Public

### Responses

**200 OK**

```json
[
    {
        "id": 1,
        "name": "Tithe",
        "description": "General tithe donation",
        "created_by": 1,
        "created_by_email": "admin@example.com",
        "created_by_name": "Admin User",
        "created_at": "2026-08-25T19:00:00Z"
    }
]
```

---

## 2. Create Public Donation

Create a donation transaction publicly. No authentication required.

### Endpoint

- **URL:** `/api/donation/public/donate/`
- **Method:** `POST`
- **Auth:** Public

### Payload

```json
{
    "donation_type_id": 1,
    "donor_name": "John Doe",
    "donor_email": "john@example.com",
    "phone_number": "254712345678",
    "amount": 100.00
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type_id` | integer | Yes | ID of the `DonationType` to donate to |
| `donor_name` | string | Yes | Full name of the donor |
| `donor_email` | string | Yes | Email address of the donor |
| `phone_number` | string | Yes | M-Pesa registered phone number |
| `amount` | decimal | Yes | Amount to donate |

### Responses

**201 Created**

```json
{
    "id": 1,
    "donation_type": 1,
    "donation_type_name": "Tithe",
    "user": null,
    "user_email": null,
    "phone_number": "254712345678",
    "amount": "100.00",
    "donor_name": "John Doe",
    "donor_email": "john@example.com",
    "status": "PENDING",
    "mpesa_receipt": null,
    "merchant_request_id": null,
    "checkout_request_id": null,
    "transaction_desc": "Public donation for Tithe",
    "created_at": "2026-08-26T00:00:00Z",
    "updated_at": "2026-08-26T00:00:00Z"
}
```

**400 Bad Request**

```json
{
    "donation_type_id": ["This field is required."],
    "donor_name": ["This field is required."]
}
```

**404 Not Found**

```json
{
    "detail": "Donation type not found."
}
```

---

## 3. Admin Donation Types

Admin-only endpoints to manage donation types.

### Endpoints

- **URL:** `/api/donation/donation-types/`
- **Method:** `GET`, `POST`
- **Auth:** Admin user

- **URL:** `/api/donation/donation-types/{id}/`
- **Method:** `GET`, `PUT`, `PATCH`, `DELETE`
- **Auth:** Admin user

---

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
    "donation_type_id": 1,
    "phone_number": "254712345678",
    "amount": 100.00,
    "donor_name": "John Doe",
    "donor_email": "john@example.com"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type_id` | integer | Yes | ID of the `DonationType` to pay for |
| `phone_number` | string | Yes | M-Pesa registered phone number |
| `amount` | decimal | Yes | Amount to donate |
| `donor_name` | string | No | Name of the donor. If omitted, system will try to look up the name from previous transactions with the same phone number |
| `donor_email` | string | No | Email of the donor |

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
        "donor_name": "John Doe",
        "donor_email": "john@example.com",
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

## 1.1 Prompt Payment (STK Push)

Prompts a user to make a payment via M-Pesa STK Push to a specific donation type account.

### Endpoint

- **URL:** `/api/payments/prompt/`
- **Method:** `POST`
- **Auth:** Public

### Payload

```json
{
    "donation_type_id": 1,
    "phone_number": "254712345678",
    "amount": 100.00,
    "donor_name": "John Doe",
    "donor_email": "john@example.com"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type_id` | integer | Yes | ID of the `DonationType` account to pay into |
| `phone_number` | string | Yes | M-Pesa registered phone number |
| `amount` | decimal | Yes | Amount to prompt the user to pay |
| `donor_name` | string | No | Name of the donor |
| `donor_email` | string | No | Email of the donor |

### Responses

**200 OK**

```json
{
    "success": true,
    "message": "Payment prompt sent successfully. Please check your phone to complete the KSh 100.00 payment for Tithe.",
    "data": {
        "transaction_id": 1,
        "donation_type": "Tithe",
        "amount": "100.00",
        "phone_number": "254712345678",
        "donor_name": "John Doe",
        "donor_email": "john@example.com",
        "checkout_request_id": "ws_CO_123456789",
        "status": "PENDING"
    }
}
```

**400 Bad Request**

```json
{
    "detail": "donation_type_id, phone_number, and amount are required."
}
```

or

```json
{
    "detail": "Amount must be a positive number."
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
    "detail": "Error connecting to M-Pesa: <error message>"
}
```

---

## 1.2 Lookup Phone Number

Look up a donor's registered name by phone number from previous transactions. This allows the treasurer to identify the account holder before prompting a payment.

### Endpoint

- **URL:** `/api/payments/lookup-phone/`
- **Method:** `POST`
- **Auth:** Public

### Payload

```json
{
    "phone_number": "254712345678"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `phone_number` | string | Yes | M-Pesa registered phone number to look up |

### Responses

**200 OK (Found)**

```json
{
    "success": true,
    "phone": "254712345678",
    "donor_name": "John Doe",
    "donor_email": "john@example.com",
    "last_transaction_id": 42,
    "last_transaction_date": "2026-08-25T19:00:00Z"
}
```

**200 OK (Not Found)**

```json
{
    "success": true,
    "phone": "254712345678",
    "donor_name": null,
    "donor_email": null,
    "last_transaction_id": null,
    "last_transaction_date": null,
    "message": "No previous transaction found for this phone number."
}
```

**400 Bad Request**

```json
{
    "detail": "phone_number is required."
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
    "donor_name": "John Doe",
    "donor_email": "john@example.com",
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
        "donor_name": "John Doe",
        "donor_email": "john@example.com",
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

Retrieve, update, or delete a single transaction by ID. Admin-only.

### Endpoint

- **URL:** `/api/payments/transactions/{id}/`
- **Method:** `GET`, `PUT`, `PATCH`, `DELETE`
- **Auth:** Admin user

### GET Response

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
    "donor_name": "John Doe",
    "donor_email": "john@example.com",
    "payment_method": "MPESA",
    "status": "SUCCESS",
    "mpesa_receipt": "ABC123",
    "merchant_request_id": "12345-1",
    "checkout_request_id": "ws_CO_123456789",
    "transaction_desc": "Payment for Tithe",
    "created_at": "2026-08-25T19:00:00Z",
    "updated_at": "2026-08-25T19:00:01Z"
}
```

### PUT/PATCH Request

Update one or more fields of the transaction.

```json
{
    "amount": 2000.00,
    "donor_name": "Jane Doe",
    "status": "SUCCESS"
}
```

### PUT/PATCH Response

**200 OK**

```json
{
    "id": 1,
    "donation_type": 1,
    "donation_type_name": "Tithe",
    "user": null,
    "user_email": null,
    "phone_number": "254712345678",
    "amount": "2000.00",
    "donor_name": "Jane Doe",
    "donor_email": "john@example.com",
    "payment_method": "MPESA",
    "status": "SUCCESS",
    "mpesa_receipt": "ABC123",
    "merchant_request_id": "12345-1",
    "checkout_request_id": "ws_CO_123456789",
    "transaction_desc": "Payment for Tithe",
    "created_at": "2026-08-25T19:00:00Z",
    "updated_at": "2026-08-26T07:30:00Z"
}
```

### DELETE Response

**204 No Content**

No response body.

---

## 7. Resend Receipt (Admin)

Resend the payment receipt email with PDF attachment to the donor. Admin-only.

### Endpoint

- **URL:** `/api/payments/transactions/resend-receipt/`
- **Method:** `POST`
- **Auth:** Admin user

### Payload

```json
{
    "transaction_id": 1
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `transaction_id` | integer | Yes | ID of the transaction to resend receipt for |

### Responses

**200 OK**

```json
{
    "detail": "Receipt resent successfully.",
    "email": "john@example.com"
}
```

**400 Bad Request**

```json
{
    "detail": "transaction_id is required."
}
```

or

```json
{
    "detail": "Transaction has no donor email."
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
    "detail": "Transaction not found."
}
```

**500 Internal Server Error**

```json
{
    "detail": "Failed to send receipt: <error message>"
}
```

---

## 8. Donation Type Statistics (Admin)

Get aggregated statistics for all donation type accounts. Admin-only.

### Endpoint

- **URL:** `/api/payments/stats/donation-types/`
- **Method:** `GET`
- **Auth:** Admin user

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
