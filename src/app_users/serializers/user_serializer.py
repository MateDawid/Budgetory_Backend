from django.contrib.auth import get_user_model
from rest_framework import serializers

from app_users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Class for serializing User model."""

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "username")
        read_only_fields = ("id",)

    def to_representation(self, instance: User):
        """
        Extends model representation with "value" and "label" fields for React MUI DataGrid filtering purposes.

        Attributes:
            instance [AbstractUser]: AbstractUser model instance

        Returns:
            OrderedDict: Dictionary containing additional fields.
        """
        representation = super().to_representation(instance)
        representation["value"] = instance.id
        representation["label"] = instance.username
        return representation
