from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ['email', 'username', 'pin_setup_complete', 'failed_login_attempts', 'is_active']
    search_fields = ['email', 'username']
    list_filter = ['is_active', 'pin_setup_complete']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Security', {'fields': ('pin', 'pin_setup_complete', 'failed_login_attempts', 'lockout_until')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active'),
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'last_login']
