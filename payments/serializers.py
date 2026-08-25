from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    donation_type_name = serializers.CharField(source='donation_type.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'donation_type', 'donation_type_name', 'user', 'user_email',
            'phone_number', 'amount', 'donor_name', 'donor_email',
            'status', 'mpesa_receipt', 'merchant_request_id', 'checkout_request_id',
            'transaction_desc', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'mpesa_receipt', 'merchant_request_id', 'checkout_request_id', 'created_at', 'updated_at']
