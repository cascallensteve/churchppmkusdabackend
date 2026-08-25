from rest_framework import serializers
from .models import DonationType


class DonationTypeSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = DonationType
        fields = ['id', 'name', 'description', 'created_by', 'created_by_email', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PublicDonationSerializer(serializers.Serializer):
    donation_type_id = serializers.IntegerField()
    donor_name = serializers.CharField(max_length=255)
    donor_email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
