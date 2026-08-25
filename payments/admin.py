from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'donation_type_name', 'user_email', 'phone_number', 'amount', 'status', 'mpesa_receipt', 'created_at']
    list_select_related = ['donation_type', 'user']
    search_fields = ['phone_number', 'mpesa_receipt', 'merchant_request_id', 'checkout_request_id']
    list_filter = ['status', 'created_at', 'donation_type']
    readonly_fields = ['created_at', 'updated_at', 'merchant_request_id', 'checkout_request_id']

    def donation_type_name(self, obj):
        return obj.donation_type.name
    donation_type_name.short_description = 'Donation Type'

    def user_email(self, obj):
        return obj.user.email if obj.user else '-'
    user_email.short_description = 'User'
