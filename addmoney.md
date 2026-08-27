# Add Funds to Donation Type

Admin endpoint to add funds to a donation type account.

**Base URL:** `/api/payments/adjust/`

---

## Request

**Method:** `POST`

**Auth:** Admin user required

**Payload:**

```json
{
    "donation_type": 1,
    "amount": 5000.00,
    "reason": "Bank deposit correction"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `donation_type` | integer | Yes | ID of the `DonationType` account to add funds to |
| `amount` | decimal | Yes | Amount to add. Must be greater than zero |
| `reason` | string | Yes | Reason for the adjustment |

---

## Response

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

| Field | Type | Description |
|---|---|---|
| `id` | integer | Adjustment ID |
| `donation_type` | integer | Donation type ID |
| `amount` | decimal | Amount added |
| `reason` | string | Reason for adjustment |
| `created_by` | integer | Admin user ID who made the adjustment |
| `created_by_email` | string | Email of the admin who made the adjustment |
| `new_balance` | decimal | New balance after the adjustment |
| `created_at` | string | Timestamp when the adjustment was made |

---

## Error Responses

**400 Bad Request - Amount must be greater than zero:**

```json
{
    "amount": ["Amount must be greater than zero."]
}
```

**400 Bad Request - Missing fields:**

```json
{
    "donation_type": ["This field is required."],
    "amount": ["This field is required."]
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
    "detail": "Donation type not found."
}
```

---

## Example Usage

### cURL

```bash
curl -X POST https://your-domain.com/api/payments/adjust/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "donation_type": 1,
    "amount": 5000.00,
    "reason": "Bank deposit correction"
  }'
```

### JavaScript / Axios

```javascript
const response = await axios.post(
  'https://your-domain.com/api/payments/adjust/',
  {
    donation_type: 1,
    amount: 5000.00,
    reason: 'Bank deposit correction'
  },
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

console.log(response.data);
```

---

## Notes

- This endpoint adds funds directly to a donation type account balance
- The balance is recalculated automatically after the adjustment
- All adjustments are logged with the admin who made the change
- Use this for manual corrections, bank deposits, or other balance adjustments that are not tied to a specific transaction
