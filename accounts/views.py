from django.contrib.auth.hashers import make_password
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
    UserSerializer,
    ProfileSerializer,
)
from accounts.models import User


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
