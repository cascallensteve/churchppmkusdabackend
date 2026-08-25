from django.urls import path
from . import views

urlpatterns = [
    path('public/', views.public_donation_types_view, name='public-donation-types'),
    path('public/donate/', views.public_donation_create_view, name='public-donation-create'),
    path('donation-types/', views.DonationTypeListCreateView.as_view(), name='donation-type-list-create'),
    path('donation-types/<int:pk>/', views.DonationTypeDetailView.as_view(), name='donation-type-detail'),
]
