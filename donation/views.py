from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import DonationType
from .serializers import DonationTypeSerializer, PublicDonationSerializer


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class DonationTypeListCreateView(generics.ListCreateAPIView):
    queryset = DonationType.objects.all()
    serializer_class = DonationTypeSerializer
    permission_classes = [IsAdminUser]


class DonationTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DonationType.objects.all()
    serializer_class = DonationTypeSerializer
    permission_classes = [IsAdminUser]


@api_view(['GET'])
@permission_classes([AllowAny])
def public_donation_types_view(request):
    donation_types = DonationType.objects.all()
    serializer = DonationTypeSerializer(donation_types, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def public_donation_create_view(request):
    serializer = PublicDonationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        donation_type = DonationType.objects.get(id=data['donation_type_id'])
    except DonationType.DoesNotExist:
        return Response(
            {'detail': 'Donation type not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    from payments.models import Transaction
    transaction = Transaction.objects.create(
        donation_type=donation_type,
        donor_name=data['donor_name'],
        donor_email=data['donor_email'],
        phone_number=data['phone_number'],
        amount=data['amount'],
        transaction_desc=f"Public donation for {donation_type.name}",
    )

    from payments.serializers import TransactionSerializer
    return Response(
        TransactionSerializer(transaction).data,
        status=status.HTTP_201_CREATED,
    )
