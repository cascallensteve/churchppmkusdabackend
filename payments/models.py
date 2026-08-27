from django.db import models
from django.conf import settings
from donation.models import DonationType


class Transaction(models.Model):
    MPESA = 'MPESA'
    CASH = 'CASH'

    PAYMENT_METHOD_CHOICES = [
        (MPESA, 'M-Pesa'),
        (CASH, 'Cash'),
    ]

    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
        (CANCELLED, 'Cancelled'),
    ]

    donation_type = models.ForeignKey(DonationType, on_delete=models.PROTECT, related_name='transactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    donor_name = models.CharField(max_length=255, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default=MPESA)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    mpesa_receipt = models.CharField(max_length=100, blank=True, null=True)
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    transaction_desc = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.donation_type.name} - {self.phone_number} - {self.amount}"


class Allocation(models.Model):
    donation_type = models.ForeignKey(DonationType, on_delete=models.PROTECT, related_name='allocations')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    allocated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='allocations')
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.EmailField(blank=True, null=True)
    purpose = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.donation_type.name} - {self.amount} - {self.recipient_name}"


class Expense(models.Model):
    donation_type = models.ForeignKey(DonationType, on_delete=models.PROTECT, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.donation_type.name} - {self.amount} - {self.description}"
