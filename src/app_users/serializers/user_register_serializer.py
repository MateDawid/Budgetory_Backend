from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class UserRegisterSerializer(serializers.ModelSerializer):
    """Class for serializing User model instances during creation."""

    password_1 = serializers.CharField(write_only=True, min_length=8)
    password_2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "password_1", "password_2")
        read_only_fields = ("id",)

    def validate(self, attrs: dict) -> dict:
        """
        Validates input parameters.

        Args:
            attrs [dict]: Input parameters.

        Returns:
            dict: Validated parameters.

        Raises:
            ValidationError: Raised when password_1 and password_2 are not the same.
        """
        if attrs["password_1"] != attrs["password_2"]:
            raise ValidationError("Provided passwords are not the same.")
        return attrs

    def create(self, validated_data: dict) -> AbstractBaseUser:
        """
        Creates User database object after input data validation.

        Args:
            validated_data [dict]: Validated input data.

        Returns:
            AbstractBaseUser: Newly created User model instance.
        """
        data = {key: value for key, value in validated_data.items() if key not in ("password_1", "password_2")}
        data["password"] = validated_data["password_1"]
        return self.Meta.model.objects.create_user(**data)
