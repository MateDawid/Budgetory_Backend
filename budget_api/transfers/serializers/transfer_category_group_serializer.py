from rest_framework import serializers
from transfers.models.transfer_category_group_model import TransferCategoryGroup


class TransferCategoryGroupSerializer(serializers.ModelSerializer):
    """Serializer for TransferCategory."""

    class Meta:
        model = TransferCategoryGroup
        fields = ['id', 'name', 'description', 'transfer_type']
        read_only_fields = ['id']
