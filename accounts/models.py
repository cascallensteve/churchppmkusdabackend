from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
