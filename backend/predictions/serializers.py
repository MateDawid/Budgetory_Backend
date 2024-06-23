from collections import OrderedDict

from django.db.models import Model
from predictions.models import ExpensePrediction
from rest_framework import serializers


class ExpensePredictionSerializer(serializers.ModelSerializer):
    """Serializer for ExpensePrediction model."""

    class Meta:
        model: Model = ExpensePrediction
        fields = ('id', 'period', 'category', 'value', 'description')
        read_only_fields = ['id']

    def to_representation(self, instance: ExpensePrediction) -> OrderedDict:
        """
        Returns human-readable values of ExpensePrediction period and category.

        Attributes:
            instance [ExpensePrediction]: ExpensePrediction model instance

        Returns:
            OrderedDict: Dictionary containing readable ExpensePrediction period and category.
        """
        representation = super().to_representation(instance)
        representation['period'] = instance.period.name
        representation['category'] = instance.category.name
        return representation
