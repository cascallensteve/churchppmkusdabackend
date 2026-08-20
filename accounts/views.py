from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from accounts.serializers import (
    EmailLoginSerializer,
    PinLoginSerializer,
    SetPinSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    ProfileSerializer,
)
from accounts.models import User, PasswordResetToken


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email', '').lower().strip()
    password = request.data.get('password')
    pin = request.data.get('pin')

    if password:
        serializer = EmailLoginSerializer(data={'email': email, 'password': password})
    elif pin:
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
@permission_classes([AllowAny])
def forgot_password_view(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    user = User.objects.get(email=email)

    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
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
