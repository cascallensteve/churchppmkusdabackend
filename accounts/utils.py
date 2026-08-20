import re
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings


def hash_pin(pin: str) -> str:
    return make_password(pin)


def verify_pin(raw_pin: str, encoded_pin: str) -> bool:
    if not encoded_pin or not raw_pin:
        return False
    return check_password(raw_pin, encoded_pin)


def validate_pin_format(pin: str) -> bool:
    return bool(re.fullmatch(r'\d{4,6}', pin))


def is_locked(user) -> bool:
    if not user.lockout_until:
        return False
    return datetime.now(user.lockout_until.tzinfo) < user.lockout_until


def increment_failed_attempts(user) -> int:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.LOGIN_ATTEMPT_LIMIT:
        user.lockout_until = datetime.now() + timedelta(seconds=settings.LOGIN_LOCKOUT_DURATION)
        user.failed_login_attempts = settings.LOGIN_ATTEMPT_LIMIT
    user.save(update_fields=['failed_login_attempts', 'lockout_until'])
    return user.failed_login_attempts


def reset_failed_attempts(user):
    user.failed_login_attempts = 0
    user.lockout_until = None
    user.save(update_fields=['failed_login_attempts', 'lockout_until'])


def get_remaining_attempts(user) -> int:
    if is_locked(user):
        return 0
    return max(0, settings.LOGIN_ATTEMPT_LIMIT - user.failed_login_attempts)


def get_lockout_remaining_seconds(user) -> int | None:
    if not is_locked(user):
        return None
    delta = user.lockout_until - datetime.now(user.lockout_until.tzinfo)
    return max(0, int(delta.total_seconds()))
