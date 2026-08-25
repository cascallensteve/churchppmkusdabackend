import requests
from django.conf import settings
from datetime import datetime

class MpesaService:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')
        self.callback_url = settings.MPESA_CALLBACK_URL

        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
        if response.status_code != 200:
            raise Exception(
                f"M-Pesa OAuth failed ({response.status_code}): {response.text}"
            )
        return response.json().get('access_token')

    def initiate_stk_push(self, phone_number, amount, account_ref, transaction_desc):
        token = self.get_access_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self._generate_password(timestamp)

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_ref,
            "TransactionDesc": transaction_desc,
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def _generate_password(self, timestamp):
        raw_password = f"{self.shortcode}{self.passkey}{timestamp}"
        import base64
        return base64.b64encode(raw_password.encode()).decode()
