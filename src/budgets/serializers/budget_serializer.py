from rest_framework.serializers import ModelSerializer

from budgets.models import Budget


class BudgetSerializer(ModelSerializer):
    """Serializer for Budget model."""

    class Meta:
        model = Budget
        fields = ["id", "name", "description", "currency", "members"]
        read_only_fields = ["id"]
