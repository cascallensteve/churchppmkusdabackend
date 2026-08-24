from django.urls import path
from . import views

urlpatterns = [
    path('donation-types/', views.DonationTypeListCreateView.as_view(), name='donation-type-list-create'),
    path('donation-types/<int:pk>/', views.DonationTypeDetailView.as_view(), name='donation-type-detail'),
]
