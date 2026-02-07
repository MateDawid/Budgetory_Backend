from datetime import date

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from periods.models import Period
from periods.models.choices.period_status import PeriodStatus
from periods.serializers.period_serializer import PeriodSerializer


def periods_url(wallet_id):
    """Creates and returns Wallet Periods URL."""
    return reverse("wallets:period-list", args=[wallet_id])


def period_detail_url(wallet_id, period_id):
    """Creates and returns Period detail URL."""
    return reverse("wallets:period-detail", args=[wallet_id, period_id])


@pytest.mark.django_db
class TestPeriodFilterSetOrdering:
    """Tests for ordering with PeriodFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        ("id", "name", "status", "-status", "date_start", "date_end", "-id", "-name", "-date_start", "-date_end"),
    )
    def test_get_periods_list_sorted_by_single_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five Period objects created in database.
        WHEN: The PeriodViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Period existing in database sorted by given param.
        """
        wallet = wallet_factory(owner=base_user)
        for _ in range(5):
            period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(wallet.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        periods = Period.objects.all().order_by(sort_param)
        serializer = PeriodSerializer(periods, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(periods) == 5
        assert response.data == serializer.data


@pytest.mark.django_db
class TestPeriodFilterSetFiltering:
    """Tests for filtering with PeriodFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some period",
            "SOME PERIOD",
            "some period",
            "SoMe PeRiOd",
            "Some",
            "some",
            "SOME",
            "Period",
            "period",
            "PERIOD",
        ),
    )
    def test_get_periods_list_filtered_by_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two Period objects for single Wallet.
        WHEN: The PeriodViewSet list view is called with "name" filter.
        THEN: Response must contain all Period existing in database assigned to Wallet containing given
        "name" value in name param.
        """
        wallet = wallet_factory(owner=base_user)
        matching_period = period_factory(wallet=wallet, name="Some period")
        period_factory(wallet=wallet, name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(wallet.id), data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Period.objects.all().count() == 2
        periods = Period.objects.filter(id=matching_period.id)
        serializer = PeriodSerializer(
            periods,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == periods.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_period.id

    @pytest.mark.parametrize("date_param", ("date_start", "date_end"))
    def test_get_periods_list_filtered_by_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        date_param: str,
    ):
        """
        GIVEN: Two Period model objects for single Wallet with different dates assigned.
        WHEN: The PeriodViewSet list view is called with date filter.
        THEN: Response contains all Periods existing in database assigned to Wallet matching given
        date value.
        """
        wallet = wallet_factory(owner=base_user)
        other_date_start, other_date_end = date(year=2024, month=10, day=1), date(year=2024, month=10, day=31)
        matching_date_start, matching_date_end = date(year=2024, month=11, day=1), date(year=2024, month=11, day=30)

        period_factory(wallet=wallet, date_start=other_date_start, date_end=other_date_end)
        period = period_factory(wallet=wallet, date_start=matching_date_start, date_end=matching_date_end)
        api_client.force_authenticate(base_user)

        payload = (
            {"date_start_after": "2024-11-01", "date_start_before": "2024-11-01"}
            if date_param == "date_start"
            else {"date_end_after": "2024-11-30", "date_end_before": "2024-11-30"}
        )
        response = api_client.get(periods_url(wallet.id), data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert Period.objects.all().count() == 2
        periods = Period.objects.filter(date_start=matching_date_start)
        serializer = PeriodSerializer(
            periods,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == periods.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == period.id

    def test_get_periods_list_filtered_by_status(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Period objects for single Wallet - one with status = PeriodStatus.ACTIVE,
        one with status = PeriodStatus.CLOSED.
        WHEN: The PeriodViewSet list view is called with status filter.
        THEN: Response must contain all Period existing in database with specified status value.
        """
        wallet = wallet_factory(owner=base_user)
        period_factory(
            wallet=wallet,
            status=PeriodStatus.CLOSED,
            date_start=date(year=2024, month=10, day=1),
            date_end=date(year=2024, month=10, day=31),
        )
        period = period_factory(
            wallet=wallet,
            status=PeriodStatus.ACTIVE,
            date_start=date(year=2024, month=11, day=1),
            date_end=date(year=2024, month=11, day=30),
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(wallet.id), data={"status": PeriodStatus.ACTIVE})

        assert response.status_code == status.HTTP_200_OK
        assert Period.objects.all().count() == 2
        periods = Period.objects.filter(status=PeriodStatus.ACTIVE)
        serializer = PeriodSerializer(
            periods,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == periods.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == period.id
