import logging
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.db.models import Sum, Count, Q
from .models import Transaction, Allocation
from donation.models import DonationType
from .serializers import TransactionSerializer, AdminCashTransactionSerializer, AllocationSerializer, ManualDonationSerializer, ExpenseSerializer
from .services import MpesaService
from .pdf_utils import generate_receipt_pdf

logger = logging.getLogger(__name__)


mpesa_service = MpesaService()


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return Transaction.objects.all()


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = Transaction.objects.all()


@api_view(['POST'])
@permission_classes([AllowAny])
def initiate_payment_view(request):
    donation_type_id = request.data.get('donation_type_id')
    phone_number = request.data.get('phone_number')
    amount = request.data.get('amount')
    donor_name = request.data.get('donor_name')
    donor_email = request.data.get('donor_email')

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
            donor_name=donor_name,
            donor_email=donor_email,
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


@api_view(['POST'])
@permission_classes([AllowAny])
def prompt_payment_view(request):
    donation_type_id = request.data.get('donation_type_id')
    phone_number = request.data.get('phone_number')
    amount = request.data.get('amount')
    donor_name = request.data.get('donor_name', '').strip()
    donor_email = request.data.get('donor_email', '').strip()

    if not donation_type_id or not phone_number or not amount:
        missing = []
        if not donation_type_id:
            missing.append('donation_type_id')
        if not phone_number:
            missing.append('phone_number')
        if not amount:
            missing.append('amount')
        return Response(
            {'detail': f'Required fields missing: {", ".join(missing)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return Response(
            {'detail': 'Amount must be a positive number.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        donation_type = DonationType.objects.get(id=donation_type_id)
    except DonationType.DoesNotExist:
        return Response(
            {'detail': 'Donation type not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not donor_name:
        previous = Transaction.objects.filter(
            phone_number=phone_number,
            donor_name__isnull=False
        ).exclude(donor_name='').order_by('-created_at').first()
        if previous:
            donor_name = previous.donor_name
            donor_email = donor_email or previous.donor_email

    try:
        transaction = Transaction.objects.create(
            donation_type=donation_type,
            phone_number=phone_number,
            amount=amount,
            donor_name=donor_name or None,
            donor_email=donor_email or None,
            payment_method=Transaction.MPESA,
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
                'success': True,
                'message': f'Payment prompt sent successfully. Please check your phone to complete the KSh {amount:,.2f} payment for {donation_type.name}.',
                'data': {
                    'transaction_id': transaction.id,
                    'donation_type': donation_type.name,
                    'amount': f'{amount:,.2f}',
                    'phone_number': phone_number,
                    'donor_name': donor_name or None,
                    'donor_email': donor_email or None,
                    'checkout_request_id': transaction.checkout_request_id,
                    'status': 'PENDING',
                }
            }, status=status.HTTP_200_OK)
        else:
            transaction.status = Transaction.FAILED
            transaction.save(update_fields=['status'])
            return Response(
                {'detail': 'Failed to initiate payment. Please try again.', 'success': False},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        transaction.status = Transaction.FAILED
        transaction.save(update_fields=['status'])
        return Response(
            {'detail': f'Error connecting to M-Pesa: {str(e)}', 'success': False},
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

            if transaction.donor_email:
                try:
                    context = {
                        'transaction': transaction,
                        'donor_name': transaction.donor_name or 'Donor',
                        'donor_email': transaction.donor_email,
                        'mpesa_receipt': mpesa_receipt,
                        'payment_method': transaction.get_payment_method_display(),
                    }
                    subject = 'Payment Receipt - MKUSD Church Treasury'
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to_email = [transaction.donor_email]

                    text_content = render_to_string('payments/emails/transaction_success.txt', context)
                    html_content = render_to_string('payments/emails/transaction_success.html', context)

                    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                    msg.attach_alternative(html_content, "text/html")

                    pdf_content = generate_receipt_pdf(transaction, transaction.donor_name, transaction.donor_email, mpesa_receipt)
                    msg.attach(f'receipt_{transaction.id}.pdf', pdf_content, 'application/pdf')

                    msg.send(fail_silently=False)
                    logger.info(f"Receipt email sent successfully for transaction {transaction.id} to {transaction.donor_email}")
                except Exception as e:
                    logger.error(f"Failed to send receipt email for transaction {transaction.id}: {str(e)}")
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


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def resend_receipt_view(request):
    transaction_id = request.data.get('transaction_id')

    if not transaction_id:
        return Response(
            {'detail': 'transaction_id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except Transaction.DoesNotExist:
        return Response(
            {'detail': 'Transaction not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not transaction.donor_email:
        return Response(
            {'detail': 'Transaction has no donor email.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        context = {
            'transaction': transaction,
            'donor_name': transaction.donor_name or 'Donor',
            'donor_email': transaction.donor_email,
            'mpesa_receipt': transaction.mpesa_receipt,
            'payment_method': transaction.get_payment_method_display(),
        }
        subject = 'Payment Receipt - MKUSD Church Treasury'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [transaction.donor_email]

        text_content = render_to_string('payments/emails/transaction_success.txt', context)
        html_content = render_to_string('payments/emails/transaction_success.html', context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")

        pdf_content = generate_receipt_pdf(transaction, transaction.donor_name, transaction.donor_email, transaction.mpesa_receipt)
        msg.attach(f'receipt_{transaction.id}.pdf', pdf_content, 'application/pdf')

        msg.send(fail_silently=False)

        return Response(
            {'detail': 'Receipt resent successfully.', 'email': transaction.donor_email},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {'detail': f'Failed to send receipt: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_cash_transaction_view(request):
    serializer = AdminCashTransactionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    transaction = serializer.save()

    if transaction.donor_email:
        try:
            context = {
                'transaction': transaction,
                'donor_name': transaction.donor_name or 'Donor',
                'donor_email': transaction.donor_email,
                'mpesa_receipt': None,
                'payment_method': transaction.get_payment_method_display(),
            }
            subject = 'Payment Receipt - MKUSD Church Treasury'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [transaction.donor_email]

            text_content = render_to_string('payments/emails/transaction_success.txt', context)
            html_content = render_to_string('payments/emails/transaction_success.html', context)

            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            msg.attach_alternative(html_content, "text/html")

            pdf_content = generate_receipt_pdf(transaction, transaction.donor_name, transaction.donor_email, None)
            msg.attach(f'receipt_{transaction.id}.pdf', pdf_content, 'application/pdf')

            msg.send(fail_silently=False)
            logger.info(f"Cash transaction receipt email sent for transaction {transaction.id} to {transaction.donor_email}")
        except Exception as e:
            logger.error(f"Failed to send cash transaction receipt email for transaction {transaction.id}: {str(e)}")

    return Response(
        {
            'detail': 'Cash transaction created successfully.',
            'transaction': TransactionSerializer(transaction).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def manual_donation_view(request):
    serializer = ManualDonationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    transaction = serializer.save()

    if transaction.donor_email:
        try:
            context = {
                'transaction': transaction,
                'donor_name': transaction.donor_name or 'Donor',
                'donor_email': transaction.donor_email,
                'mpesa_receipt': None,
                'payment_method': transaction.get_payment_method_display(),
            }
            subject = 'Payment Receipt - MKUSD Church Treasury'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [transaction.donor_email]

            text_content = render_to_string('payments/emails/transaction_success.txt', context)
            html_content = render_to_string('payments/emails/transaction_success.html', context)

            msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            msg.attach_alternative(html_content, "text/html")

            pdf_content = generate_receipt_pdf(transaction, transaction.donor_name, transaction.donor_email, None)
            msg.attach(f'receipt_{transaction.id}.pdf', pdf_content, 'application/pdf')

            msg.send(fail_silently=False)
            logger.info(f"Manual donation receipt email sent for transaction {transaction.id} to {transaction.donor_email}")
        except Exception as e:
            logger.error(f"Failed to send manual donation receipt email for transaction {transaction.id}: {str(e)}")

    return Response(
        {
            'detail': 'Manual donation entry created successfully.',
            'transaction': TransactionSerializer(transaction).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def spend_funds_view(request):
    serializer = ExpenseSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    expense = serializer.save()

    return Response(
        {
            'detail': 'Expense recorded successfully.',
            'expense': ExpenseSerializer(expense).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def allocate_funds_view(request):
    serializer = AllocationSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    allocation = serializer.save()

    return Response(
        {
            'detail': 'Funds allocated successfully.',
            'allocation': AllocationSerializer(allocation).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def lookup_phone_view(request):
    phone_number = request.data.get('phone_number', '').strip()

    if not phone_number:
        return Response(
            {'detail': 'phone_number is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    transaction = Transaction.objects.filter(
        phone_number=phone_number,
        donor_name__isnull=False
    ).exclude(donor_name='').order_by('-created_at').first()

    if transaction:
        return Response({
            'success': True,
            'phone': phone_number,
            'donor_name': transaction.donor_name,
            'donor_email': transaction.donor_email,
            'last_transaction_id': transaction.id,
            'last_transaction_date': transaction.created_at,
        }, status=status.HTTP_200_OK)

    return Response({
        'success': True,
        'phone': phone_number,
        'donor_name': None,
        'donor_email': None,
        'last_transaction_id': None,
        'last_transaction_date': None,
        'message': 'No previous transaction found for this phone number.',
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def donation_stats_view(request):
    donation_types = DonationType.objects.all().order_by('name')
    stats = []

    for dt in donation_types:
        transactions = Transaction.objects.filter(donation_type=dt)
        allocations = Allocation.objects.filter(donation_type=dt)

        total_transactions = transactions.count()
        successful_transactions = transactions.filter(status=Transaction.SUCCESS).count()
        pending_transactions = transactions.filter(status=Transaction.PENDING).count()
        failed_transactions = transactions.filter(status=Transaction.FAILED).count()
        cancelled_transactions = transactions.filter(status=Transaction.CANCELLED).count()

        successful_txns = transactions.filter(status=Transaction.SUCCESS)
        total_amount_received = successful_txns.aggregate(total=Sum('amount'))['total'] or 0
        cash_amount = successful_txns.filter(payment_method=Transaction.CASH).aggregate(total=Sum('amount'))['total'] or 0
        mpesa_amount = successful_txns.filter(payment_method=Transaction.MPESA).aggregate(total=Sum('amount'))['total'] or 0

        total_allocated = allocations.aggregate(total=Sum('amount'))['total'] or 0

        stats.append({
            'id': dt.id,
            'name': dt.name,
            'description': dt.description,
            'current_balance': dt.balance or 0,
            'total_transactions': total_transactions,
            'successful_transactions': successful_transactions,
            'pending_transactions': pending_transactions,
            'failed_transactions': failed_transactions,
            'cancelled_transactions': cancelled_transactions,
            'total_amount_received': total_amount_received,
            'cash_amount': cash_amount,
            'mpesa_amount': mpesa_amount,
            'total_allocated': total_allocated,
        })

    return Response(stats, status=status.HTTP_200_OK)
