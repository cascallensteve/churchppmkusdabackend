from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import DonationType
from .serializers import DonationTypeSerializer


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
