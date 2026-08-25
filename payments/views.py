from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from .models import Transaction
from .serializers import TransactionSerializer
from .services import MpesaService


mpesa_service = MpesaService()


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Transaction.objects.all()


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Transaction.objects.all()


@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_payment_view(request):
    donation_type_id = request.data.get('donation_type_id')
    phone_number = request.data.get('phone_number')
    amount = request.data.get('amount')

    if not donation_type_id or not phone_number or not amount:
        return Response(
            {'detail': 'donation_type_id, phone_number, and amount are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from donation.models import DonationType
        donation_type = DonationType.objects.get(id=donation_type_id)
    except DonationType.DoesNotExist:
        return Response(
            {'detail': 'Donation type not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        transaction = Transaction.objects.create(
            donation_type=donation_type,
            phone_number=phone_number,
            amount=amount,
            transaction_desc=f"Payment for {donation_type.name}",
        )
    except Exception as e:
        return Response(
            {'detail': f'Failed to create transaction: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        response = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_ref=donation_type.name,
            transaction_desc=f"Payment for {donation_type.name}",
        )

        if response.get('ResponseCode') == '0':
            transaction.merchant_request_id = response.get('MerchantRequestID')
            transaction.checkout_request_id = response.get('CheckoutRequestID')
            transaction.save(update_fields=['merchant_request_id', 'checkout_request_id'])

            return Response({
                'message': 'Payment initiated successfully. Please check your phone.',
                'checkout_request_id': transaction.checkout_request_id,
                'transaction': TransactionSerializer(transaction).data,
            }, status=status.HTTP_200_OK)
        else:
            transaction.status = Transaction.FAILED
            transaction.save(update_fields=['status'])
            return Response(
                {'detail': 'Failed to initiate payment. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        transaction.status = Transaction.FAILED
        transaction.save(update_fields=['status'])
        return Response(
            {'detail': f'Error connecting to M-Pesa: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_validation_view(request):
    return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def mpesa_callback_view(request):
    body = request.data.get('Body', {})
    stk_callback = body.get('stkCallback', {})
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc')

    transactions = Transaction.objects.filter(checkout_request_id=checkout_request_id)
    if not transactions.exists():
        return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=status.HTTP_200_OK)

    for transaction in transactions:
        if result_code == 0:
            metadata = stk_callback.get('CallbackMetadata', {})
            items = metadata.get('Item', [])
            mpesa_receipt = None
            for item in items:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')

            transaction.status = Transaction.SUCCESS
            transaction.mpesa_receipt = mpesa_receipt
            transaction.save(update_fields=['status', 'mpesa_receipt'])
        else:
            transaction.status = Transaction.FAILED
            transaction.save(update_fields=['status'])

    return Response({"ResultCode": 0, "ResultDesc": "Accepted"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def payment_status_view(request):
    checkout_request_id = request.query_params.get('checkout_request_id')

    if not checkout_request_id:
        return Response(
            {'detail': 'checkout_request_id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        transaction = Transaction.objects.filter(checkout_request_id=checkout_request_id).order_by('-created_at').first()
        if not transaction:
            return Response(
                {'detail': 'Transaction not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'detail': f'Error fetching transaction: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
