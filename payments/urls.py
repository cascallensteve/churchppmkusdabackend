from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.initiate_payment_view, name='initiate-payment'),
    path('validation/', views.mpesa_validation_view, name='mpesa-validation'),
    path('callback/', views.mpesa_callback_view, name='mpesa-callback'),
    path('status/', views.payment_status_view, name='payment-status'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
]
