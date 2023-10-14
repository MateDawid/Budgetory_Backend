import pytest
from app_users.tests.factories import UserFactory
from pytest_django.lazy_django import skip_if_no_django
from pytest_factoryboy import register
from rest_framework.test import APIClient, APIRequestFactory

register(UserFactory)


@pytest.fixture(scope='session')
def api_rf() -> APIRequestFactory:
    skip_if_no_django()
    return APIRequestFactory()


@pytest.fixture(scope='session')
def api_client() -> APIClient:
    skip_if_no_django()
    return APIClient()
