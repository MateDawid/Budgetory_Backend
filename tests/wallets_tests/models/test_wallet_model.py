import pytest
from django.contrib.auth.models import AbstractUser
from django.db import DataError
from factory.base import FactoryMetaClass

from wallets.models.wallet_model import Wallet


@pytest.mark.django_db
class TestWalletModel:
    """Tests for Wallet model"""

    def test_create_object(self, user_factory: FactoryMetaClass):
        """
        GIVEN: User model instance in database.
        WHEN: Wallet instance create attempt with valid data.
        THEN: Wallet model instance exists in database with given data.
        """
        payload = {
            "name": "Home wallet",
            "description": "Wallet with home expenses and incomes",
            "owner": user_factory(),
        }
        wallet = Wallet.objects.create(**payload)
        for param, value in payload.items():
            assert getattr(wallet, param) == value
        assert str(wallet) == wallet.name

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, user: AbstractUser):
        """
        GIVEN: User model instance in database.
        WHEN: Wallet instance create attempt with name too long.
        THEN: DataError raised. Object not created in database.
        """
        max_length = Wallet._meta.get_field("name").max_length
        payload = {
            "name": (max_length + 1) * "a",
            "description": "Wallet with home expenses and incomes",
        }

        with pytest.raises(DataError) as exc:
            Wallet.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Wallet.objects.filter(name=payload["name"]).exists()
