from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.initiate_payment_view, name='initiate-payment'),
    path('prompt/', views.prompt_payment_view, name='prompt-payment'),
    path('lookup-phone/', views.lookup_phone_view, name='lookup-phone'),
    path('validation/', views.mpesa_validation_view, name='mpesa-validation'),
    path('callback/', views.mpesa_callback_view, name='mpesa-callback'),
    path('status/', views.payment_status_view, name='payment-status'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('transactions/resend-receipt/', views.resend_receipt_view, name='resend-receipt'),
    path('transactions/cash/', views.admin_cash_transaction_view, name='admin-cash-transaction'),
    path('allocate/', views.allocate_funds_view, name='allocate-funds'),
    path('stats/donation-types/', views.donation_stats_view, name='donation-stats'),
]
