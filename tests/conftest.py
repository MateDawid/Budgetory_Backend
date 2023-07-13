import pytest
from pytest_django.lazy_django import skip_if_no_django
from pytest_factoryboy import register

from tests.factories import UserFactory

register(UserFactory)


@pytest.fixture(scope='session')
def api_rf():
    skip_if_no_django()
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()
