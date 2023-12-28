from datetime import date
from typing import Any

import pytest
from django.urls import reverse
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

    def test_retrieve_periods_list(self, api_client: APIClient, base_user: Any):
        """Test retrieving list of periods"""
        api_client.force_authenticate(base_user)
        payload_1 = {
            'name': '2023_01',
            'user': base_user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        payload_2 = {
            'name': '2023_02',
            'user': base_user,
            'date_start': date(2023, 2, 1),
            'date_end': date(2023, 2, 28),
        }
        BudgetingPeriod.objects.create(**payload_1)
        BudgetingPeriod.objects.create(**payload_2)

        response = api_client.get(PERIODS_URL)

        periods = BudgetingPeriod.objects.all().order_by('-date_start')
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_recipe_list_limited_to_user(self, api_client: APIClient, user_factory):
        """Test list of periods is limited to authenticated user."""
        user_1 = user_factory()
        user_2 = user_factory()
        payload_1 = {
            'name': '2023_01',
            'user': user_1,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        payload_2 = {
            'name': '2023_01',
            'user': user_2,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        BudgetingPeriod.objects.create(**payload_1)
        BudgetingPeriod.objects.create(**payload_2)
        api_client.force_authenticate(user_1)

        response = api_client.get(PERIODS_URL)

        periods = BudgetingPeriod.objects.filter(user=user_1)
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data
