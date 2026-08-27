
Endpoint: POST /api/payments/transactions/resend-receipt/ Auth: Admin only

Request payload:

{ "transaction_id": 1 }
Response (200 OK):

{ "detail": "Receipt resent successfully.", "email": "john@example.com" }
It regenerates the receipt email with th