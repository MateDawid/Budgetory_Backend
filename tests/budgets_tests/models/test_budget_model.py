import pytest
from django.contrib.auth.models import AbstractUser
from django.db import DataError
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget


@pytest.mark.django_db
class TestBudgetModel:
    """Tests for Budget model"""

    def test_create_object(self, user_factory: FactoryMetaClass):
        """
        GIVEN: User model instance in database.
        WHEN: Budget instance create attempt with valid data.
        THEN: Budget model instance exists in database with given data.
        """
        members = [user_factory() for _ in range(3)]
        payload = {
            "name": "Home budget",
            "description": "Budget with home expenses and incomes",
            "currency": "PLN",
        }
        budget = Budget.objects.create(**payload)
        budget.members.add(*members)
        for param, value in payload.items():
            assert getattr(budget, param) == value
        assert budget.members.all().count() == 3
        assert str(budget) == budget.name

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, user: AbstractUser):
        """
        GIVEN: User model instance in database.
        WHEN: Budget instance create attempt with name too long.
        THEN: DataError raised. Object not created in database.
        """
        max_length = Budget._meta.get_field("name").max_length
        payload = {
            "name": (max_length + 1) * "a",
            "description": "Budget with home expenses and incomes",
            "currency": "PLN",
        }

        with pytest.raises(DataError) as exc:
            Budget.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Budget.objects.filter(name=payload["name"]).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_currency_too_long(self, user: AbstractUser):
        """
        GIVEN: User model instance in database.
        WHEN: Budget instance create attempt with currency too long.
        THEN: DataError raised. Object not created in database.
        """
        max_length = Budget._meta.get_field("currency").max_length
        payload = {
            "name": "Home budget",
            "description": "Budget with home expenses and incomes",
            "currency": (max_length + 100) * "a",
        }
        with pytest.raises(DataError) as exc:
            Budget.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Budget.objects.filter(currency=payload["currency"]).exists()
