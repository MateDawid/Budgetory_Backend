import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from src.app_users.serializers import UserSerializer


@pytest.mark.django_db
class TestUserSerializer:
    """Tests for file validation in UserSerializer."""

    payload = {
        'email': 'test@example.com',
        'password': 'pass1',
        'name': 'Test',
    }

    def test_create_user_successful(self):
        """Test successful user creation."""
        serializer = UserSerializer(data=self.payload)
        assert serializer.is_valid(raise_exception=True)
        assert 'password' not in serializer.data
        serializer.create(serializer.validated_data)
        user = UserSerializer.Meta.model.objects.get(email=self.payload['email'])
        assert user.check_password(self.payload['password'])
        assert user.name == self.payload['name']

    @pytest.mark.django_db(transaction=True)
    def test_user_with_email_exists(self):
        """Test error returned if user email exists."""
        serializer = UserSerializer(data=self.payload)
        assert serializer.is_valid(raise_exception=True)
        serializer.create(serializer.validated_data)
        with pytest.raises(IntegrityError):
            serializer.create(self.payload)
        assert UserSerializer.Meta.model.objects.filter(email=self.payload['email']).count() == 1

    def test_user_with_password_too_short(self):
        """Test an error is returned if password less than 5 chars."""
        payload = self.payload.copy()
        payload['password'] = 'pw'
        serializer = UserSerializer(data=payload)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert exc.value.detail['password'][0].code == 'min_length'
        assert str(exc.value.detail['password'][0]) == 'Ensure this field has at least 5 characters.'

    @pytest.mark.parametrize('param', ['email', 'password', 'name'])
    def test_user_with_param_not_given(self, param: str):
        """Test an error is returned if param not given."""
        payload = self.payload.copy()
        del payload[param]
        serializer = UserSerializer(data=payload)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert exc.value.detail[param][0].code == 'required'

    @pytest.mark.parametrize(
        'param, value', [('email', 'new@example.com'), ('password', 'newpass123'), ('name', 'New name')]
    )
    def test_user_update_successful(self, param: str, value: str):
        """Test update user param."""
        user = get_user_model().objects.create_user(**self.payload)
        user_id = user.id
        payload = self.payload.copy()
        payload[param] = value
        serializer = UserSerializer(instance=user)
        serializer.update(serializer.instance, payload)
        assert user.id == user_id
        if param == 'password':
            assert user.check_password(value)
        else:
            assert getattr(user, param) == value
