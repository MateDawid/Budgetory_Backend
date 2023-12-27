from periods.models import BudgetingPeriod
from rest_framework import serializers


class BudgetingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for BudgetingPeriod."""

    class Meta:
        model = BudgetingPeriod
        fields = ['id', 'user', 'name', 'date_start', 'date_end', 'is_active']
        read_only_fields = ['id']
