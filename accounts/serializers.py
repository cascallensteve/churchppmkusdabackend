from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import User, PasswordResetToken, PinResetToken
from accounts.utils import (
    hash_pin,
    verify_pin,
    validate_pin_format,
    is_locked,
    increment_failed_attempts,
    reset_failed_attempts,
    get_remaining_attempts,
    get_lockout_remaining_seconds,
)
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'pin_setup_complete', 'created_at']
        read_only_fields = ['id', 'email', 'created_at']


class ProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'profile_picture',
            'pin_setup_complete', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.save()
        return instance


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password', '')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'Invalid credentials.'})

        if is_locked(user):
            seconds = get_lockout_remaining_seconds(user)
            raise serializers.ValidationError({
                'detail': f'Account locked. Try again in {seconds} seconds.',
                'lockout_remaining': seconds,
            })

        if not user.check_password(password):
            attempts = increment_failed_attempts(user)
            remaining = get_remaining_attempts(user)
            if remaining == 0:
                seconds = get_lockout_remaining_seconds(user)
                raise serializers.ValidationError({
                    'detail': f'Account locked after {settings.LOGIN_ATTEMPT_LIMIT} failed attempts. Try again in {seconds} seconds.',
                    'lockout_remaining': seconds,
                })
            raise serializers.ValidationError({
                'detail': f'Invalid credentials. {remaining} attempts remaining.',
                'remaining_attempts': remaining,
            })

        reset_failed_attempts(user)
        attrs['user'] = user
        return attrs


class PinLoginSerializer(serializers.Serializer):
    access = serializers.CharField(required=False, allow_blank=True)
    pin = serializers.CharField(write_only=True)

    def validate(self, attrs):
        access_token = attrs.get('access', '').strip()
        pin = attrs.get('pin', '')

        if not validate_pin_format(pin):
            raise serializers.ValidationError({'pin': 'PIN must be 4-6 digits.'})

        user = None

        if access_token:
            try:
                token = AccessToken(access_token)
                user_id = token['user_id']
                user = User.objects.get(id=user_id)
            except (TokenError, InvalidToken, User.DoesNotExist):
                raise serializers.ValidationError({'access': 'Invalid or expired access token.'})
        else:
            raise serializers.ValidationError({'access': 'Access token is required for PIN login.'})

        if is_locked(user):
            seconds = get_lockout_remaining_seconds(user)
            raise serializers.ValidationError({
                'detail': f'Account locked. Try again in {seconds} seconds.',
                'lockout_remaining': seconds,
            })

        if not user.pin or not verify_pin(pin, user.pin):
            attempts = increment_failed_attempts(user)
            remaining = get_remaining_attempts(user)
            if remaining == 0:
                seconds = get_lockout_remaining_seconds(user)
                raise serializers.ValidationError({
                    'detail': f'Account locked after {settings.LOGIN_ATTEMPT_LIMIT} failed attempts. Try again in {seconds} seconds.',
                    'lockout_remaining': seconds,
                })
            raise serializers.ValidationError({
                'detail': f'Invalid PIN. {remaining} attempts remaining.',
                'remaining_attempts': remaining,
            })

        if not user.pin:
            raise serializers.ValidationError({'pin': 'PIN not set for this user.'})

        reset_failed_attempts(user)
        attrs['user'] = user
        return attrs


class SetPinSerializer(serializers.Serializer):
    pin = serializers.CharField(write_only=True, min_length=4, max_length=6)

    def validate_pin(self, value):
        if not validate_pin_format(value):
            raise serializers.ValidationError('PIN must be 4-6 digits.')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePinSerializer(serializers.Serializer):
    old_pin = serializers.CharField(write_only=True, min_length=4, max_length=6)
    new_pin = serializers.CharField(write_only=True, min_length=4, max_length=6)

    def validate_old_pin(self, value):
        if not validate_pin_format(value):
            raise serializers.ValidationError('Old PIN must be 4-6 digits.')
        return value

    def validate_new_pin(self, value):
        if not validate_pin_format(value):
            raise serializers.ValidationError('New PIN must be 4-6 digits.')
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('No user found with this email address.')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ForgotPinSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('No user found with this email address.')
        return value


class ResetPinSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_pin = serializers.CharField(write_only=True, min_length=4, max_length=6)

    def validate_new_pin(self, value):
        if not validate_pin_format(value):
            raise serializers.ValidationError('PIN must be 4-6 digits.')
        return value
