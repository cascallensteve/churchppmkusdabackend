from django.contrib import admin
from .models import DonationType


@admin.register(DonationType)
class DonationTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by_email', 'created_at']
    list_select_related = ['created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_by', 'created_at']

    def created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else '-'
    created_by_email.short_description = 'Created By'
    created_by_email.admin_order_field = 'created_by__email'
