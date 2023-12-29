from datetime import date
from typing import Any

import pytest
from django.urls import reverse
from factory.base import FactoryMetaClass
from periods.models import BudgetingPeriod
from periods.serializers import BudgetingPeriodSerializer
from rest_framework import status
from rest_framework.test import APIClient

PERIODS_URL = reverse('periods:budgetingperiod-list')


def period_detail_url(period_id):
    """Create and return a budgeting period detail URL."""
    return reverse('recipe:budgetingperiod-detail', args=[period_id])


@pytest.mark.django_db
class TestBudgetingPeriodViewSet:
    """Tests for BudgetingPeriodViewSet."""

    def test_auth_required(self, api_client: APIClient):
        """Test auth is required to call endpoint."""
        res = api_client.get(PERIODS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_periods_list(
        self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass
    ):
        """Test retrieving list of periods"""
        api_client.force_authenticate(base_user)
        budgeting_period_factory(
            user=base_user, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31), is_active=False
        )
        budgeting_period_factory(
            user=base_user, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28), is_active=True
        )

        response = api_client.get(PERIODS_URL)

        periods = BudgetingPeriod.objects.all().order_by('-date_start')
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_periods_list_limited_to_user(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budgeting_period_factory: FactoryMetaClass
    ):
        """Test list of periods is limited to authenticated user."""
        user = user_factory()
        budgeting_period_factory(user=user)
        budgeting_period_factory()
        api_client.force_authenticate(user)

        response = api_client.get(PERIODS_URL)

        periods = BudgetingPeriod.objects.filter(user=user)
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data
