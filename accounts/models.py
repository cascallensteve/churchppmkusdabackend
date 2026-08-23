from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets


class User(AbstractUser):
    email = models.EmailField(unique=True)
    pin = models.CharField(max_length=128, blank=True, null=True)
    pin_setup_complete = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
    profile_picture = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.email}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user.email}"

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at


class PinResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pin_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"PIN reset token for {self.user.email}"

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    @classmethod
    def create_for_user(cls, user):
        return cls.objects.create(
            user=user,
            token=secrets.token_hex(32),
            expires_at=timezone.now() + timedelta(hours=1),
        )
