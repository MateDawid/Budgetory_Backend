from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Class for serializing User model."""

    class Meta:
        model = get_user_model()
        fields = ("id", "email")
        read_only_fields = ("id",)
