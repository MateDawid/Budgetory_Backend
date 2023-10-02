import pytest
from pytest_django.lazy_django import skip_if_no_django
from pytest_factoryboy import register
from rest_framework.test import APIRequestFactory
from users.tests.factories import UserFactory

register(UserFactory)


@pytest.fixture(scope='session')
def api_rf() -> APIRequestFactory:
    skip_if_no_django()
    return APIRequestFactory()
