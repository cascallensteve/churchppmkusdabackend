from rest_framework import serializers
from .models import Transaction, Allocation


class TransactionSerializer(serializers.ModelSerializer):
    donation_type_name = serializers.CharField(source='donation_type.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'donation_type', 'donation_type_name', 'user', 'user_email',
            'phone_number', 'amount', 'donor_name', 'donor_email',
            'payment_method', 'status', 'mpesa_receipt', 'merchant_request_id',
            'checkout_request_id', 'transaction_desc', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'mpesa_receipt', 'merchant_request_id', 'checkout_request_id', 'created_at', 'updated_at']


class AdminCashTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'donation_type', 'phone_number', 'amount',
            'donor_name', 'donor_email', 'transaction_desc'
        ]

    def create(self, validated_data):
        validated_data['payment_method'] = Transaction.CASH
        validated_data['status'] = Transaction.SUCCESS
        return super().create(validated_data)


class ManualDonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'donation_type', 'phone_number', 'amount',
            'donor_name', 'donor_email', 'payment_method', 'transaction_desc'
        ]

    def create(self, validated_data):
        validated_data['status'] = Transaction.SUCCESS
        return super().create(validated_data)


class AllocationSerializer(serializers.ModelSerializer):
    allocated_by_email = serializers.EmailField(source='allocated_by.email', read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Allocation
        fields = [
            'id', 'donation_type', 'amount', 'allocated_by', 'allocated_by_email',
            'recipient_name', 'recipient_email', 'purpose', 'remaining_balance',
            'created_at'
        ]
        read_only_fields = ['id', 'allocated_by', 'allocated_by_email', 'remaining_balance', 'created_at']

    def validate(self, data):
        donation_type = data.get('donation_type')
        amount = data.get('amount')

        if donation_type and amount:
            if amount <= 0:
                raise serializers.ValidationError({'amount': 'Amount must be greater than zero.'})

            current_balance = donation_type.balance or 0
            if amount > current_balance:
                raise serializers.ValidationError({
                    'detail': f'Insufficient funds. Current balance: {current_balance}, requested: {amount}'
                })

        return data

    def create(self, validated_data):
        validated_data['allocated_by'] = self.context['request'].user
        allocation = super().create(validated_data)

        donation_type = allocation.donation_type
        donation_type.balance = (donation_type.balance or 0) - allocation.amount
        donation_type.save(update_fields=['balance'])

        return allocation
