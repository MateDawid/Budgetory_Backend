from typing import Any

import pytest
from app_users_tests.factories import UserFactory
from budgets_tests.factories import BudgetFactory, BudgetingPeriodFactory
from categories_tests.factories import TransferCategoryFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from entities_tests.factories import DepositFactory, EntityFactory
from predictions_tests.factories import ExpensePredictionFactory
from pytest_django.lazy_django import skip_if_no_django
from pytest_factoryboy import register
from rest_framework.test import APIClient
from transfers_tests.factories import ExpenseFactory, IncomeFactory, TransferFactory
from wallets_tests.factories.wallet_deposit_factory import WalletDepositFactory
from wallets_tests.factories.wallet_factory import WalletFactory

from app_users.models import User

register(UserFactory)
register(BudgetFactory)
register(BudgetingPeriodFactory)
register(DepositFactory)
register(EntityFactory)
register(TransferCategoryFactory)
register(ExpensePredictionFactory)
register(TransferFactory)
register(IncomeFactory)
register(ExpenseFactory)
register(WalletFactory)
register(WalletDepositFactory)


@pytest.fixture
def api_client() -> APIClient:
    """API Client for creating request."""
    skip_if_no_django()
    return APIClient()


@pytest.fixture
def base_user() -> Any:
    """User with base permissions."""
    return get_user_model().objects.create_user("user@example.com", "User", "user123!@#")


@pytest.fixture
def superuser() -> Any:
    """User with admin permissions."""
    return get_user_model().objects.create_superuser("admin@example.com", "Admin", "admin123!@#")


def get_jwt_access_token(user: User | None = None) -> str:
    """
    Function to retrieve JWT access token for existing on newly created User for test purposes.

    Args:
        user (User | None): User model instance or None

    Returns:
        str: JWT access token.
    """
    if user is None:
        user_payload = {"email": "jwt@example.com", "username": "JWT", "password": "p4ssw0rd!"}
        get_user_model().objects.create_user(**user_payload)
    else:
        raw_password = "p4ssw0rd!"
        user.set_password(raw_password)
        user.save()
        user_payload = {"email": user.email, "username": user.username, "password": raw_password}
    login_response = APIClient().post(reverse("app_users:login"), data=user_payload)
    return login_response.data["access"]
