from rest_framework import serializers


class UncategorizedExpensePredictionSerializer(serializers.Serializer):
    """Serializer for ExpensePrediction model with None value for category field."""

    category_deposit = serializers.CharField(read_only=True)
    category_priority = serializers.CharField(read_only=True, default="❗Not categorized")
    initial_plan = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    current_result = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    current_plan = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    current_funds_left = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    current_progress = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    previous_plan = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    previous_result = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    previous_funds_left = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
