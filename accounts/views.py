import secrets
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from accounts.serializers import (
    EmailLoginSerializer,
    PinLoginSerializer,
    SetPinSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ForgotPinSerializer,
    ResetPinSerializer,
    UserSerializer,
    ProfileSerializer,
)
from accounts.models import User, PasswordResetToken, PinResetToken
from accounts.utils import (
    is_locked,
    verify_pin,
    increment_failed_attempts,
    reset_failed_attempts,
    get_remaining_attempts,
    get_lockout_remaining_seconds,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email', '').lower().strip()
    password = request.data.get('password')
    pin = request.data.get('pin')
    access_token = request.data.get('access', '').strip()

    if password:
        serializer = EmailLoginSerializer(data={'email': email, 'password': password})
    elif pin:
        header_token = _get_bearer_token(request)
        if header_token:
            serializer = PinLoginSerializer(data={'access': header_token, 'pin': pin})
        elif access_token:
            serializer = PinLoginSerializer(data={'access': access_token, 'pin': pin})
        else:
            serializer = PinLoginSerializer(data={'email': email, 'pin': pin})
    else:
        return Response(
            {'detail': 'Provide either password or pin.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    access['email'] = user.email
    access['full_name'] = user.get_full_name()

    return Response({
        'access': str(access),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
        'pin_setup_required': not user.pin_setup_complete,
    }, status=status.HTTP_200_OK)


def _get_bearer_token(request):
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:].strip()
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_me_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user

    if request.method == 'GET':
        serializer = ProfileSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    partial = request.method == 'PATCH'
    serializer = ProfileSerializer(user, data=request.data, partial=partial, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_pin_view(request):
    serializer = SetPinSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    pin = serializer.validated_data['pin']

    request.user.pin = make_password(pin)
    request.user.pin_setup_complete = True
    request.user.save(update_fields=['pin', 'pin_setup_complete'])

    return Response(
        {'detail': 'PIN set successfully.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_pin_view(request):
    serializer = ChangePinSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    old_pin = serializer.validated_data['old_pin']
    new_pin = serializer.validated_data['new_pin']

    if not request.user.pin_setup_complete:
        return Response(
            {'detail': 'PIN not set. Please set a PIN first.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not verify_pin(old_pin, request.user.pin):
        return Response(
            {'old_pin': 'Incorrect current PIN.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request.user.pin = make_password(new_pin)
    request.user.save(update_fields=['pin'])

    return Response(
        {'detail': 'PIN changed successfully.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    old_password = serializer.validated_data['old_password']
    new_password = serializer.validated_data['new_password']

    if not request.user.check_password(old_password):
        return Response(
            {'old_password': 'Incorrect current password.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request.user.set_password(new_password)
    request.user.save(update_fields=['password'])
    return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_pin_view(request):
    pin = request.data.get('pin')

    if not pin:
        return Response(
            {'detail': 'PIN is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user

    if is_locked(user):
        seconds = get_lockout_remaining_seconds(user)
        return Response(
            {'detail': f'Account locked. Try again in {seconds} seconds.', 'lockout_remaining': seconds},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.pin_setup_complete or not verify_pin(pin, user.pin):
        attempts = increment_failed_attempts(user)
        remaining = get_remaining_attempts(user)
        if remaining == 0:
            seconds = get_lockout_remaining_seconds(user)
            return Response(
                {'detail': f'Account locked after {settings.LOGIN_ATTEMPT_LIMIT} failed attempts. Try again in {seconds} seconds.', 'lockout_remaining': seconds},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': f'Invalid PIN. {remaining} attempts remaining.', 'remaining_attempts': remaining},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reset_failed_attempts(user)

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    access['email'] = user.email
    access['full_name'] = user.get_full_name()

    return Response({
        'access': str(access),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    user = User.objects.get(email=email)

    token = secrets.token_hex(32)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

    PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=timezone.now() + timedelta(hours=1),
    )

    reset_url = f"{settings.FRONTEND_URL}/reset-password?uidb64={uidb64}&token={token}"

    subject = 'MKUSD Treasury - Password Reset Request'
    message = render_to_string('accounts/emails/password_reset_email.txt', {
        'user': user,
        'reset_url': reset_url,
    })

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        return Response(
            {'detail': 'Failed to send reset email.', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {'detail': 'Password reset email sent successfully.', 'email': user.email},
        status=status.HTTP_200_OK,
    )



@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']

    token_obj = PasswordResetToken.objects.filter(token=token, used=False).first()
    if not token_obj:
        return Response(
            {'detail': 'Invalid or expired reset token.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not token_obj.is_valid():
        return Response(
            {'detail': 'Reset token has expired or already been used.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = token_obj.user
    user.set_password(new_password)
    user.save(update_fields=['password'])

    token_obj.used = True
    token_obj.save(update_fields=['used'])

    return Response(
        {'detail': 'Password reset successful.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_pin_view(request):
    serializer = ForgotPinSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    user = User.objects.get(email=email)

    pin_token = PinResetToken.create_for_user(user)

    reset_url = f"{settings.FRONTEND_URL}/reset-pin?token={pin_token.token}"

    subject = 'MKUSD Treasury - PIN Reset Request'
    message = render_to_string('accounts/emails/pin_reset_email.txt', {
        'user': user,
        'reset_url': reset_url,
    })

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        return Response(
            {'detail': 'Failed to send PIN reset email.', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {'detail': 'PIN reset email sent successfully.', 'email': user.email},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_pin_view(request):
    serializer = ResetPinSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data['token']
    new_pin = serializer.validated_data['new_pin']

    token_obj = PinResetToken.objects.filter(token=token, used=False).first()
    if not token_obj:
        return Response(
            {'detail': 'Invalid or expired reset token.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not token_obj.is_valid():
        return Response(
            {'detail': 'PIN reset token has expired or already been used.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = token_obj.user
    user.pin = make_password(new_pin)
    user.pin_setup_complete = True
    user.save(update_fields=['pin', 'pin_setup_complete'])

    token_obj.used = True
    token_obj.save(update_fields=['used'])

    return Response(
        {'detail': 'PIN reset successful.'},
        status=status.HTTP_200_OK,
    )
