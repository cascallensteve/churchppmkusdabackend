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
    path('manual-donation/', views.manual_donation_view, name='manual-donation'),
    path('spend/', views.spend_funds_view, name='spend-funds'),
    path('adjust/', views.adjust_funds_view, name='adjust-funds'),
    path('allocate/', views.allocate_funds_view, name='allocate-funds'),
    path('adjustments/', views.AdjustmentListCreateView.as_view(), name='adjustment-list'),
    path('adjustments/<int:pk>/', views.AdjustmentDetailView.as_view(), name='adjustment-detail'),
    path('expenses/', views.ExpenseListCreateView.as_view(), name='expense-list'),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view(), name='expense-detail'),
    path('allocations/', views.AllocationListCreateView.as_view(), name='allocation-list'),
    path('allocations/<int:pk>/', views.AllocationDetailView.as_view(), name='allocation-detail'),
    path('stats/donation-types/', views.donation_stats_view, name='donation-stats'),
]
