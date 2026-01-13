"""
Tests for PeriodViewSet:
* TestPeriodViewSetList - GET on list view.
* TestPeriodViewSetCreate - POST on list view.
* TestPeriodViewSetDetail - GET on detail view.
* TestPeriodViewSetUpdate - PATCH on detail view.
* TestPeriodViewSetDelete - DELETE on detail view.
"""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from categories.models.choices.category_type import CategoryType
from periods.models.choices.period_status import PeriodStatus
from periods.models.period_model import Period
from periods.serializers.period_serializer import PeriodSerializer
from periods.views.period_viewset import sum_period_transfers
from predictions.models import ExpensePrediction
from transfers.models import Transfer
from wallets.models.wallet_model import Wallet


def periods_url(wallet_id):
    """Creates and returns Wallet Periods URL."""
    return reverse("wallets:period-list", args=[wallet_id])


def period_detail_url(wallet_id, period_id):
    """Creates and returns Period detail URL."""
    return reverse("wallets:period-detail", args=[wallet_id, period_id])


@pytest.mark.django_db
class TestPeriodViewSetList:
    """Tests for PeriodViewSet list view."""

    def test_auth_required(self, wallet: Wallet, api_client: APIClient):
        """
        GIVEN: Wallet model instance in database created.
        WHEN: PeriodViewSet list view called without authentication.
        THEN: Unauthorized HTTP status returned.
        """
        url = periods_url(wallet.id)

        res = api_client.get(url)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: PeriodViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = periods_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten Period model instances for single Wallet created in database.
        WHEN: PeriodViewSet called by Wallet member without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        wallet = wallet_factory(members=[base_user])
        for _ in range(10):
            period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 10

    def test_get_response_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten Period model instances for single Wallet created in database.
        WHEN: PeriodViewSet called by Wallet member with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        wallet = wallet_factory(members=[base_user])
        for _ in range(10):
            period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(wallet.id), data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_retrieve_periods_list_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Periods for Wallet in database created.
        WHEN: PeriodViewSet list view for Wallet id called by authenticated Wallet owner.
        THEN: List of Periods for given Wallet id sorted from newest to oldest returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        periods = [
            period_factory(
                wallet=wallet, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31), status=PeriodStatus.CLOSED
            ),
            period_factory(
                wallet=wallet, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28), status=PeriodStatus.ACTIVE
            ),
        ]
        for period in periods:
            for _ in range(3):
                transfer_factory(period=period)
        url = periods_url(wallet.id)

        response = api_client.get(url)

        periods = (
            Period.objects.annotate(
                incomes_sum=sum_period_transfers(CategoryType.INCOME),
                expenses_sum=sum_period_transfers(CategoryType.EXPENSE),
            )
            .filter(wallet=wallet)
            .order_by("-date_start")
        )
        serializer = PeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == periods.count() == 2
        assert [result["id"] for result in response.data] == [result["id"] for result in serializer.data]
        for period in serializer.data:
            assert period["value"] == period["id"]
            assert period["label"] == period["name"]
            assert period["status_display"] == PeriodStatus(period["status"]).label
            assert period["incomes_sum"] == str(
                Decimal(
                    sum(
                        Transfer.objects.filter(period__id=period["id"], transfer_type=CategoryType.INCOME).values_list(
                            "value", flat=True
                        )
                    )
                ).quantize(Decimal("0.00"))
            )
            assert period["expenses_sum"] == str(
                Decimal(
                    sum(
                        Transfer.objects.filter(
                            period__id=period["id"], transfer_type=CategoryType.EXPENSE
                        ).values_list("value", flat=True)
                    )
                ).quantize(Decimal("0.00"))
            )

    def test_retrieve_periods_list_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Periods for Wallet in database created.
        WHEN: PeriodViewSet list view for Wallet id called by authenticated Wallet member.
        THEN: List of Periods for given Wallet id sorted from newest to oldest returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        period_factory(
            wallet=wallet, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31), status=PeriodStatus.CLOSED
        )
        period_factory(
            wallet=wallet, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28), status=PeriodStatus.ACTIVE
        )
        url = periods_url(wallet.id)

        response = api_client.get(url)

        periods = Period.objects.filter(wallet=wallet).order_by("-date_start")
        serializer = PeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == periods.count() == 2
        assert response.data == serializer.data

    def test_periods_list_limited_to_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Periods for two different Wallets in database created.
        WHEN: PeriodViewSet list view for Wallet id called by authenticated User.
        THEN: List of Periods containing only declared Wallet periods returned.
        """
        # Other period
        period_factory()
        # Auth User period
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = periods_url(wallet.id)

        response = api_client.get(url)

        periods = Period.objects.filter(wallet=wallet)
        serializer = PeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert Period.objects.all().count() == 2
        assert len(response.data) == len(serializer.data) == periods.count() == 1
        assert periods.first() == period
        assert response.data == serializer.data

    def test_ordering_by_date_start(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Three Periods for Wallet in database created.
        WHEN: PeriodViewSet list view called with ordering parameter.
        THEN: List of Periods ordered by date_start returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        period_factory(wallet=wallet, date_start=date(2023, 3, 1), date_end=date(2023, 3, 31))
        period_factory(wallet=wallet, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31))
        period_factory(wallet=wallet, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28))
        url = periods_url(wallet.id)

        response = api_client.get(url, data={"ordering": "date_start"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert response.data[0]["date_start"] == "2023-01-01"
        assert response.data[1]["date_start"] == "2023-02-01"
        assert response.data[2]["date_start"] == "2023-03-01"

    def test_fields_param_incomes_sum(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Periods with transfers in database.
        WHEN: PeriodViewSet called with fields=incomes_sum query parameter.
        THEN: Response includes incomes_sum field with correct calculation.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period_1, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("30.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("40.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("300.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("400.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("50.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("60.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"ordering": "date_start", "fields": "incomes_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("300.00")
        assert Decimal(response.data[1]["incomes_sum"]) == Decimal("700.00")

    def test_fields_param_expenses_sum(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Periods with transfers in database.
        WHEN: PeriodViewSet called with fields=expenses_sum query parameter.
        THEN: Response includes expenses_sum field with correct calculation.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period_1, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("30.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("40.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("300.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("400.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("50.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("60.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"ordering": "date_start", "fields": "expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("70.00")
        assert Decimal(response.data[1]["expenses_sum"]) == Decimal("110.00")

    def test_fields_param_both_sums(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Periods with transfers in database.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum query parameter.
        THEN: Response includes both incomes_sum and expenses_sum fields with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period_1, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("30.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("40.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("300.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("400.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("50.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("60.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(
            periods_url(wallet.id), {"ordering": "date_start", "fields": "incomes_sum,expenses_sum"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("300.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("70.00")
        assert Decimal(response.data[1]["incomes_sum"]) == Decimal("700.00")
        assert Decimal(response.data[1]["expenses_sum"]) == Decimal("110.00")

    def test_fields_param_without_sums(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Periods with transfers in database.
        WHEN: PeriodViewSet called without fields query parameter.
        THEN: Response does not include annotated incomes_sum and expenses_sum fields.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("50.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        # Fields exist in serializer with default values
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("0.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("0.00")

    def test_incomes_sum_with_no_incomes(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with only expenses (no incomes) in database.
        WHEN: PeriodViewSet called with fields=incomes_sum query parameter.
        THEN: Response includes incomes_sum field with zero value.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        expense_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("200.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("0.00")

    def test_expenses_sum_with_no_expenses(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with only incomes (no expenses) in database.
        WHEN: PeriodViewSet called with fields=expenses_sum query parameter.
        THEN: Response includes expenses_sum field with zero value.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period, value=Decimal("200.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("0.00")

    def test_sums_with_no_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with no transfers in database.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum query parameter.
        THEN: Response includes both sum fields with zero values.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet)

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("0.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("0.00")

    def test_sums_with_decimal_precision(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers having various decimal values.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum query parameter.
        THEN: Response includes sum fields with correct decimal precision (2 places).
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.99"))
        income_factory(wallet=wallet, period=period, value=Decimal("200.01"))
        expense_factory(wallet=wallet, period=period, value=Decimal("30.55"))
        expense_factory(wallet=wallet, period=period, value=Decimal("40.45"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("301.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("71.00")

    def test_sums_ordering_by_incomes_sum(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple periods with different income amounts.
        WHEN: PeriodViewSet called with ordering=incomes_sum and fields=incomes_sum.
        THEN: Response is ordered by incomes_sum in ascending order.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)
        period_3 = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period_1, value=Decimal("500.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period_3, value=Decimal("300.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"ordering": "incomes_sum", "fields": "incomes_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("100.00")
        assert Decimal(response.data[1]["incomes_sum"]) == Decimal("300.00")
        assert Decimal(response.data[2]["incomes_sum"]) == Decimal("500.00")

    def test_sums_ordering_by_expenses_sum_descending(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple periods with different expense amounts.
        WHEN: PeriodViewSet called with ordering=-expenses_sum and fields=expenses_sum.
        THEN: Response is ordered by expenses_sum in descending order.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)
        period_3 = period_factory(wallet=wallet)

        expense_factory(wallet=wallet, period=period_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("800.00"))
        expense_factory(wallet=wallet, period=period_3, value=Decimal("500.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"ordering": "-expenses_sum", "fields": "expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("800.00")
        assert Decimal(response.data[1]["expenses_sum"]) == Decimal("500.00")
        assert Decimal(response.data[2]["expenses_sum"]) == Decimal("200.00")

    def test_sums_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple periods with transfers in database.
        WHEN: PeriodViewSet called with pagination and fields=incomes_sum,expenses_sum.
        THEN: Paginated response includes sum fields with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        for i in range(5):
            period = period_factory(wallet=wallet)
            income_factory(wallet=wallet, period=period, value=Decimal(f"{(i + 1) * 100}.00"))
            expense_factory(wallet=wallet, period=period, value=Decimal(f"{(i + 1) * 50}.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(
            periods_url(wallet.id),
            {"page_size": 2, "page": 1, "ordering": "date_start", "fields": "incomes_sum,expenses_sum"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
        assert len(response.data["results"]) == 2
        assert "incomes_sum" in response.data["results"][0]
        assert "expenses_sum" in response.data["results"][0]

    def test_sums_isolated_per_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two periods with different transfers.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum.
        THEN: Each period shows only its own transfer sums, not combined.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31))
        period_2 = period_factory(wallet=wallet, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28))

        income_factory(wallet=wallet, period=period_1, value=Decimal("1000.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("500.00"))

        income_factory(wallet=wallet, period=period_2, value=Decimal("2000.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("1500.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(
            periods_url(wallet.id), {"ordering": "date_start", "fields": "incomes_sum,expenses_sum"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # Period 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("1000.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("500.00")

        # Period 2
        assert Decimal(response.data[1]["incomes_sum"]) == Decimal("2000.00")
        assert Decimal(response.data[1]["expenses_sum"]) == Decimal("1500.00")

    def test_sums_with_large_values(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with large transfer values.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum.
        THEN: Response handles large decimal values correctly.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("999999.99"))
        income_factory(wallet=wallet, period=period, value=Decimal("888888.88"))
        expense_factory(wallet=wallet, period=period, value=Decimal("777777.77"))
        expense_factory(wallet=wallet, period=period, value=Decimal("666666.66"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("1888888.87")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("1444444.43")


@pytest.mark.django_db
class TestPeriodViewSetCreate:
    """Tests for creating Period via PeriodViewSet."""

    def test_auth_required(self, wallet: Wallet, api_client: APIClient):
        """
        GIVEN: Wallet model instance in database created.
        WHEN: PeriodViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 status returned.
        """
        url = periods_url(wallet.id)

        res = api_client.post(url, data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: PeriodViewSet list endpoint called with POST.
        THEN: HTTP 400 returned - access granted, but data invalid.
        """
        wallet = wallet_factory(members=[base_user])
        url = periods_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_single_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database created.
        WHEN: PeriodViewSet list view for Wallet id called by authenticated Wallet member by POST with
        valid data.
        THEN: Period for Wallet created in database.
        """
        wallet = wallet_factory(members=[base_user])
        deposit_1 = deposit_factory(wallet=wallet)
        deposit_2 = deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        payload = {
            "name": "2023_01",
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
            "status": PeriodStatus.DRAFT,
        }
        url = periods_url(wallet.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Period.objects.filter(wallet=wallet).count() == 1
        period = Period.objects.get(id=response.data["id"])
        for key in payload:
            assert getattr(period, key) == payload[key]
        serializer = PeriodSerializer(period)
        assert response.data == serializer.data
        for deposit in (deposit_1, deposit_2):
            assert ExpensePrediction.objects.filter(
                deposit=deposit,
                category=None,
                period=period,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ).exists()

    def test_error_create_two_draft_periods_for_one_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database created.
        WHEN: PeriodViewSet list view for Wallet id called by authenticated User by POST
        with valid data two times.
        THEN: One DRAFT Period for Wallet created in database, second one not created.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload_1 = {
            "name": "2023_01",
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        payload_2 = {
            "name": "2023_02",
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 2, 1),
            "date_end": date(2023, 2, 28),
        }
        url = periods_url(wallet.id)

        response_1 = api_client.post(url, payload_1)
        response_2 = api_client.post(url, payload_2)

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_400_BAD_REQUEST
        assert response_2.data["detail"]["status"][0] == "📝 Draft period already exists in Wallet."
        assert Period.objects.filter(wallet=wallet).count() == 1

    def test_create_same_period_for_two_wallets(
        self, api_client: APIClient, base_user: AbstractUser, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Two Wallets in database created.
        WHEN: PeriodViewSet list view called for two Wallets by authenticated User by POST with valid data.
        THEN: Two Period, every for different Wallet created in database.
        """
        payload = {
            "name": "2023_01",
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        api_client.force_authenticate(base_user)
        wallet_1 = wallet_factory(members=[base_user])
        url = periods_url(wallet_1.id)
        api_client.post(url, payload)
        wallet_2 = wallet_factory(members=[base_user])
        url = periods_url(wallet_2.id)
        api_client.post(url, payload)

        all_periods_queryset = Period.objects.all()
        assert all_periods_queryset.count() == 2
        for wallet in (wallet_1, wallet_2):
            wallet_periods_queryset = all_periods_queryset.filter(wallet=wallet)
            assert wallet_periods_queryset.count() == 1

    def test_error_name_too_long(
        self, api_client: APIClient, base_user: AbstractUser, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST with name
        too long in passed data.
        THEN: Bad request 400 returned, no object in database created.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        max_length = Period._meta.get_field("name").max_length
        payload = {
            "name": (max_length + 1) * "a",
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        url = periods_url(wallet.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["detail"]
        assert response.data["detail"]["name"][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Period.objects.filter(wallet=wallet).exists()

    def test_error_name_already_used(
        self, api_client: APIClient, base_user: AbstractUser, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Period for Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST with name already used
        for existing Period in passed data.
        THEN: Bad request 400 returned, no object in database created.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = {
            "name": "2023_01",
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 2),
        }
        Period.objects.create(wallet=wallet, **payload)
        payload["date_start"] = date(2023, 1, 3)
        payload["date_end"] = date(2023, 1, 4)
        url = periods_url(wallet.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["detail"]
        assert response.data["detail"]["name"][0] == f'Period with name "{payload["name"]}" already exists in Wallet.'
        assert Period.objects.filter(wallet=wallet).count() == 1

    @pytest.mark.parametrize(
        "period_status",
        (
            pytest.param(PeriodStatus.ACTIVE, id="active"),
            pytest.param(PeriodStatus.CLOSED, id="closed"),
        ),
    )
    def test_error_new_period_status_has_to_be_draft(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_status: PeriodStatus,
    ):
        """
        GIVEN: Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST
        to create Period with not DRAFT status.
        THEN: Bad request 400 returned, period not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = {
            "name": "2023_02",
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
            "status": period_status,
        }
        url = periods_url(wallet.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data["detail"]
        assert response.data["detail"]["status"][0] == "New period has to be created with draft status."
        assert not Period.objects.exists()

    @pytest.mark.parametrize("date_start, date_end", (("", date.today()), (date.today(), ""), ("", "")))
    def test_error_date_blank(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        date_start: date | str,
        date_end: date | str,
    ):
        """
        GIVEN: Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST to create
        Period with one of or both dates blank.
        THEN: Bad request 400 returned, no object in database created.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = {"name": "2023_01", "date_start": date_start, "date_end": date_end, "status": PeriodStatus.CLOSED}
        url = periods_url(wallet.id)
        error_message = "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "date_start" in response.data["detail"] or "date_end" in response.data["detail"]
        assert (
            response.data["detail"].get("date_start", [""])[0] == error_message
            or response.data["detail"].get("date_end", [""])[0] == error_message
        )
        assert not Period.objects.filter(wallet=wallet).exists()

    def test_error_date_end_before_date_start(
        self, api_client: APIClient, base_user: AbstractUser, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST to create
        Period with date_end before date_start.
        THEN: Bad request 400 returned, no object in database created.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = {
            "name": "2023_01",
            "date_start": date(2023, 5, 1),
            "date_end": date(2023, 4, 30),
            "status": PeriodStatus.DRAFT,
        }
        url = periods_url(wallet.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert response.data["detail"]["non_field_errors"][0] == "Start date should be earlier than end date."
        assert not Period.objects.filter(wallet=wallet).exists()

    @pytest.mark.parametrize(
        "date_start, date_end",
        (
            # Date start before first existing period
            (date(2023, 5, 1), date(2023, 6, 1)),
            (date(2023, 5, 1), date(2023, 6, 15)),
            (date(2023, 5, 1), date(2023, 6, 30)),
            (date(2023, 5, 1), date(2023, 7, 1)),
            (date(2023, 5, 1), date(2023, 7, 15)),
            (date(2023, 5, 1), date(2023, 7, 31)),
            (date(2023, 5, 1), date(2023, 8, 1)),
            # Date start same as in first existing period
            (date(2023, 6, 1), date(2023, 6, 15)),
            (date(2023, 6, 1), date(2023, 6, 30)),
            (date(2023, 6, 1), date(2023, 7, 1)),
            (date(2023, 6, 1), date(2023, 7, 15)),
            (date(2023, 6, 1), date(2023, 7, 31)),
            (date(2023, 6, 1), date(2023, 8, 1)),
            # Date start between first existing period daterange
            (date(2023, 6, 15), date(2023, 6, 30)),
            (date(2023, 6, 15), date(2023, 7, 1)),
            (date(2023, 6, 15), date(2023, 7, 15)),
            (date(2023, 6, 15), date(2023, 7, 31)),
            (date(2023, 6, 15), date(2023, 8, 1)),
            # Date start same as first existing period's end date
            (date(2023, 6, 30), date(2023, 7, 1)),
            (date(2023, 6, 30), date(2023, 7, 15)),
            (date(2023, 6, 30), date(2023, 7, 31)),
            (date(2023, 6, 30), date(2023, 8, 1)),
            # Date start same as in second existing period
            (date(2023, 7, 1), date(2023, 7, 15)),
            (date(2023, 7, 1), date(2023, 7, 31)),
            (date(2023, 7, 1), date(2023, 8, 1)),
            # Date start between second existing period daterange
            (date(2023, 7, 15), date(2023, 7, 31)),
            # Date start same as second existing period's end date
            (date(2023, 7, 31), date(2023, 8, 1)),
        ),
    )
    def test_error_colliding_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        date_start: date,
        date_end: date,
    ):
        """
        GIVEN: Two Periods for Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST to create
        Period with dates colliding with existing Periods.
        THEN: Bad request 400 returned, no object in database created.
        """
        wallet = wallet_factory(members=[base_user])
        payload_1 = {
            "name": "2023_06",
            "status": PeriodStatus.CLOSED,
            "date_start": date(2023, 6, 1),
            "date_end": date(2023, 6, 30),
        }
        payload_2 = {
            "name": "2023_07",
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 7, 1),
            "date_end": date(2023, 7, 31),
        }
        payload_invalid = {
            "name": "invalid",
            "status": PeriodStatus.DRAFT,
            "date_start": date_start,
            "date_end": date_end,
        }
        Period.objects.create(wallet=wallet, **payload_1)
        Period.objects.create(wallet=wallet, **payload_2)
        api_client.force_authenticate(base_user)
        url = periods_url(wallet.id)

        response = api_client.post(url, payload_invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0] == "Period date range collides with other period in Wallet."
        )
        assert Period.objects.filter(wallet=wallet).count() == 2

    @pytest.mark.parametrize(
        "date_start, date_end",
        (
            (date(2023, 5, 1), date(2023, 5, 31)),
            (date(2022, 6, 1), date(2022, 6, 30)),
        ),
    )
    def test_error_on_create_period_in_past(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        date_start: date,
        date_end: date,
    ):
        """
        GIVEN: Two Periods for Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST to create
        Period with dates earlier than any existing Period.
        THEN: Bad request 400 returned, no object in database created.
        """
        wallet = wallet_factory(members=[base_user])
        payload = {
            "name": "2023_06",
            "status": PeriodStatus.CLOSED,
            "date_start": date(2023, 6, 1),
            "date_end": date(2023, 6, 30),
        }
        payload_invalid = {
            "name": "invalid",
            "status": PeriodStatus.DRAFT,
            "date_start": date_start,
            "date_end": date_end,
        }
        Period.objects.create(wallet=wallet, **payload)
        api_client.force_authenticate(base_user)
        url = periods_url(wallet.id)

        response = api_client.post(url, payload_invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "New period date start has to be greater than previous period date end."
        )
        assert Period.objects.filter(wallet=wallet).count() == 1

    def test_error_create_period_for_not_accessible_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database created.
        WHEN: PeriodViewSet list view called by authenticated User (not Wallet owner nor member).
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        wallet = wallet_factory(members=[other_user])
        api_client.force_authenticate(base_user)
        payload = {
            "name": "2023_01",
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        url = periods_url(wallet.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not Period.objects.filter(wallet=wallet).exists()


@pytest.mark.django_db
class TestPeriodViewSetDetail:
    """Tests for detail view in PeriodViewSet."""

    def test_auth_required(self, period: Period, api_client: APIClient):
        """
        GIVEN: Period model instance in database created.
        WHEN: PeriodViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 status returned.
        """
        url = period_detail_url(period.wallet.id, period.id)

        res = api_client.post(url)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: PeriodViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        url = period_detail_url(wallet.id, period.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_period_details_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (owner of Wallet).
        THEN: Period details returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = period_detail_url(wallet.id, period.id)

        response = api_client.get(url)
        serializer = PeriodSerializer(period)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_get_period_details_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (member of Wallet).
        THEN: Period details returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = period_detail_url(wallet.id, period.id)

        response = api_client.get(url)
        serializer = PeriodSerializer(period)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_period_details_unauthenticated(self, api_client: APIClient, period_factory: FactoryMetaClass):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        period = period_factory()
        url = period_detail_url(period.wallet.id, period.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_other_user_period_details(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (not Wallet owner
        nor member).
        THEN: Forbidden HTTP 403 returned.
        """
        user_1 = user_factory()
        user_2 = user_factory()
        period = period_factory(wallet=wallet_factory(members=[user_1]))
        api_client.force_authenticate(user_2)

        url = period_detail_url(period.wallet.id, period.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_fields_param_both_sums(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Periods with transfers in database.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum query parameter.
        THEN: Response includes both incomes_sum and expenses_sum fields with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period_1, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("30.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("40.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("300.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("400.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("50.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("60.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(
            periods_url(wallet.id), {"ordering": "date_start", "fields": "incomes_sum,expenses_sum"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("300.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("70.00")
        assert Decimal(response.data[1]["incomes_sum"]) == Decimal("700.00")
        assert Decimal(response.data[1]["expenses_sum"]) == Decimal("110.00")

    def test_fields_param_without_sums(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Periods with transfers in database.
        WHEN: PeriodViewSet called without fields query parameter.
        THEN: Response does not include annotated incomes_sum and expenses_sum fields.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("50.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        # Fields exist in serializer with default values
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("0.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("0.00")

    def test_incomes_sum_with_no_incomes(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with only expenses (no incomes) in database.
        WHEN: PeriodViewSet called with fields=incomes_sum query parameter.
        THEN: Response includes incomes_sum field with zero value.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        expense_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("200.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("0.00")

    def test_expenses_sum_with_no_expenses(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with only incomes (no expenses) in database.
        WHEN: PeriodViewSet called with fields=expenses_sum query parameter.
        THEN: Response includes expenses_sum field with zero value.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period, value=Decimal("200.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("0.00")

    def test_sums_with_no_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with no transfers in database.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum query parameter.
        THEN: Response includes both sum fields with zero values.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet)

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("0.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("0.00")

    def test_sums_with_decimal_precision(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers having various decimal values.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum query parameter.
        THEN: Response includes sum fields with correct decimal precision (2 places).
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.99"))
        income_factory(wallet=wallet, period=period, value=Decimal("200.01"))
        expense_factory(wallet=wallet, period=period, value=Decimal("30.55"))
        expense_factory(wallet=wallet, period=period, value=Decimal("40.45"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("301.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("71.00")

    def test_sums_ordering_by_incomes_sum(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple periods with different income amounts.
        WHEN: PeriodViewSet called with ordering=incomes_sum and fields=incomes_sum.
        THEN: Response is ordered by incomes_sum in ascending order.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)
        period_3 = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period_1, value=Decimal("500.00"))
        income_factory(wallet=wallet, period=period_2, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period_3, value=Decimal("300.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"ordering": "incomes_sum", "fields": "incomes_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("100.00")
        assert Decimal(response.data[1]["incomes_sum"]) == Decimal("300.00")
        assert Decimal(response.data[2]["incomes_sum"]) == Decimal("500.00")

    def test_sums_ordering_by_expenses_sum_descending(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple periods with different expense amounts.
        WHEN: PeriodViewSet called with ordering=-expenses_sum and fields=expenses_sum.
        THEN: Response is ordered by expenses_sum in descending order.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)
        period_3 = period_factory(wallet=wallet)

        expense_factory(wallet=wallet, period=period_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("800.00"))
        expense_factory(wallet=wallet, period=period_3, value=Decimal("500.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"ordering": "-expenses_sum", "fields": "expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("800.00")
        assert Decimal(response.data[1]["expenses_sum"]) == Decimal("500.00")
        assert Decimal(response.data[2]["expenses_sum"]) == Decimal("200.00")

    def test_sums_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple periods with transfers in database.
        WHEN: PeriodViewSet called with pagination and fields=incomes_sum,expenses_sum.
        THEN: Paginated response includes sum fields with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        for i in range(5):
            period = period_factory(wallet=wallet)
            income_factory(wallet=wallet, period=period, value=Decimal(f"{(i + 1) * 100}.00"))
            expense_factory(wallet=wallet, period=period, value=Decimal(f"{(i + 1) * 50}.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(
            periods_url(wallet.id),
            {"page_size": 2, "page": 1, "ordering": "date_start", "fields": "incomes_sum,expenses_sum"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
        assert len(response.data["results"]) == 2
        assert "incomes_sum" in response.data["results"][0]
        assert "expenses_sum" in response.data["results"][0]

    def test_sums_isolated_per_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two periods with different transfers.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum.
        THEN: Each period shows only its own transfer sums, not combined.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31))
        period_2 = period_factory(wallet=wallet, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28))

        income_factory(wallet=wallet, period=period_1, value=Decimal("1000.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("500.00"))

        income_factory(wallet=wallet, period=period_2, value=Decimal("2000.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("1500.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(
            periods_url(wallet.id), {"ordering": "date_start", "fields": "incomes_sum,expenses_sum"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        # Period 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("1000.00")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("500.00")

        # Period 2
        assert Decimal(response.data[1]["incomes_sum"]) == Decimal("2000.00")
        assert Decimal(response.data[1]["expenses_sum"]) == Decimal("1500.00")

    def test_sums_with_large_values(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with large transfer values.
        WHEN: PeriodViewSet called with fields=incomes_sum,expenses_sum.
        THEN: Response handles large decimal values correctly.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("999999.99"))
        income_factory(wallet=wallet, period=period, value=Decimal("888888.88"))
        expense_factory(wallet=wallet, period=period, value=Decimal("777777.77"))
        expense_factory(wallet=wallet, period=period, value=Decimal("666666.66"))

        api_client.force_authenticate(base_user)
        response = api_client.get(periods_url(wallet.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert Decimal(response.data[0]["incomes_sum"]) == Decimal("1888888.87")
        assert Decimal(response.data[0]["expenses_sum"]) == Decimal("1444444.43")


@pytest.mark.django_db
class TestPeriodViewSetDetailSumFields:
    """Tests for incomes_sum and expenses_sum fields in detail view."""

    def test_detail_with_incomes_sum_field(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers in database.
        WHEN: PeriodViewSet detail view called with fields=incomes_sum query parameter.
        THEN: Response includes incomes_sum field with correct calculation.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        income_factory(wallet=wallet, period=period, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("50.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("300.00")

    def test_detail_with_expenses_sum_field(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers in database.
        WHEN: PeriodViewSet detail view called with fields=expenses_sum query parameter.
        THEN: Response includes expenses_sum field with correct calculation.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("30.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("40.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["expenses_sum"]) == Decimal("70.00")

    def test_detail_with_both_sum_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers in database.
        WHEN: PeriodViewSet detail view called with fields=incomes_sum,expenses_sum.
        THEN: Response includes both sum fields with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("500.00"))
        income_factory(wallet=wallet, period=period, value=Decimal("250.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("150.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("100.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("750.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("250.00")

    def test_detail_without_sum_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers in database.
        WHEN: PeriodViewSet detail view called without fields query parameter.
        THEN: Response includes default sum values (not annotated).
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("100.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("50.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        # Without annotation, should return default values from serializer
        assert Decimal(response.data["incomes_sum"]) == Decimal("0.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("0.00")

    def test_detail_incomes_sum_with_no_incomes(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with only expenses (no incomes).
        WHEN: PeriodViewSet detail view called with fields=incomes_sum.
        THEN: Response includes incomes_sum with zero value.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        expense_factory(wallet=wallet, period=period, value=Decimal("100.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("0.00")

    def test_detail_expenses_sum_with_no_expenses(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with only incomes (no expenses).
        WHEN: PeriodViewSet detail view called with fields=expenses_sum.
        THEN: Response includes expenses_sum with zero value.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("200.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["expenses_sum"]) == Decimal("0.00")

    def test_detail_sums_with_no_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with no transfers.
        WHEN: PeriodViewSet detail view called with fields=incomes_sum,expenses_sum.
        THEN: Response includes both sum fields with zero values.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("0.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("0.00")

    def test_detail_sums_with_decimal_precision(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers having various decimal values.
        WHEN: PeriodViewSet detail view called with sum fields.
        THEN: Response includes sums with correct decimal precision.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("123.45"))
        income_factory(wallet=wallet, period=period, value=Decimal("678.90"))
        expense_factory(wallet=wallet, period=period, value=Decimal("12.34"))
        expense_factory(wallet=wallet, period=period, value=Decimal("56.78"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("802.35")
        assert Decimal(response.data["expenses_sum"]) == Decimal("69.12")

    def test_detail_sums_with_multiple_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with many transfers.
        WHEN: PeriodViewSet detail view called with sum fields.
        THEN: Response includes correct sum calculations for all transfers.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        # Create 10 incomes and 10 expenses
        for i in range(10):
            income_factory(wallet=wallet, period=period, value=Decimal(f"{i + 1}0.00"))
            expense_factory(wallet=wallet, period=period, value=Decimal(f"{i + 1}5.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        # Sum of 10, 20, 30, ..., 100 = 550
        assert Decimal(response.data["incomes_sum"]) == Decimal("550.00")
        # Sum of 15, 25, 35, ..., 105 = 600
        assert Decimal(response.data["expenses_sum"]) == Decimal("600.00")

    def test_detail_sums_only_for_specific_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple periods with transfers.
        WHEN: PeriodViewSet detail view called for one specific period.
        THEN: Response includes sums only for that specific period.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)

        # Period 1 transfers
        income_factory(wallet=wallet, period=period_1, value=Decimal("1000.00"))
        expense_factory(wallet=wallet, period=period_1, value=Decimal("500.00"))

        # Period 2 transfers
        income_factory(wallet=wallet, period=period_2, value=Decimal("2000.00"))
        expense_factory(wallet=wallet, period=period_2, value=Decimal("1500.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period_1.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        # Should only show period_1 sums, not period_2
        assert Decimal(response.data["incomes_sum"]) == Decimal("1000.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("500.00")

    def test_detail_sums_with_large_values(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with large transfer values.
        WHEN: PeriodViewSet detail view called with sum fields.
        THEN: Response handles large values correctly.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("9999999.99"))
        expense_factory(wallet=wallet, period=period, value=Decimal("8888888.88"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("9999999.99")
        assert Decimal(response.data["expenses_sum"]) == Decimal("8888888.88")

    def test_detail_sums_by_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with transfers for wallet where user is a member.
        WHEN: PeriodViewSet detail view called by wallet member with sum fields.
        THEN: Response includes correct sum calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)

        income_factory(wallet=wallet, period=period, value=Decimal("300.00"))
        expense_factory(wallet=wallet, period=period, value=Decimal("150.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(period_detail_url(wallet.id, period.id), {"fields": "incomes_sum,expenses_sum"})

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("300.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("150.00")

    def test_detail_sums_with_different_period_statuses(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Periods with different statuses (DRAFT, ACTIVE, CLOSED) with transfers.
        WHEN: PeriodViewSet detail view called for each period with sum fields.
        THEN: Response includes correct sums regardless of period status.
        """
        from periods.models.choices.period_status import PeriodStatus

        wallet = wallet_factory(members=[base_user])

        # Test DRAFT period
        draft_period = period_factory(wallet=wallet, status=PeriodStatus.DRAFT)
        income_factory(wallet=wallet, period=draft_period, value=Decimal("100.00"))
        expense_factory(wallet=wallet, period=draft_period, value=Decimal("50.00"))

        # Test ACTIVE period
        active_period = period_factory(wallet=wallet, status=PeriodStatus.ACTIVE)
        income_factory(wallet=wallet, period=active_period, value=Decimal("200.00"))
        expense_factory(wallet=wallet, period=active_period, value=Decimal("100.00"))

        # Test CLOSED period
        closed_period = period_factory(wallet=wallet, status=PeriodStatus.CLOSED)
        income_factory(wallet=wallet, period=closed_period, value=Decimal("300.00"))
        expense_factory(wallet=wallet, period=closed_period, value=Decimal("150.00"))

        api_client.force_authenticate(base_user)

        # Check DRAFT period
        response = api_client.get(period_detail_url(wallet.id, draft_period.id), {"fields": "incomes_sum,expenses_sum"})
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("100.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("50.00")

        # Check ACTIVE period
        response = api_client.get(
            period_detail_url(wallet.id, active_period.id), {"fields": "incomes_sum,expenses_sum"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("200.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("100.00")

        # Check CLOSED period
        response = api_client.get(
            period_detail_url(wallet.id, closed_period.id), {"fields": "incomes_sum,expenses_sum"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["incomes_sum"]) == Decimal("300.00")
        assert Decimal(response.data["expenses_sum"]) == Decimal("150.00")


@pytest.mark.django_db
class TestPeriodViewSetUpdate:
    """Tests for partial update Period via PeriodViewSet."""

    def test_auth_required(self, period: Period, api_client: APIClient):
        """
        GIVEN: Period model instance in database created.
        WHEN: PeriodViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 status returned.
        """
        url = period_detail_url(period.wallet.id, period.id)

        res = api_client.patch(url, data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: PeriodViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        url = period_detail_url(wallet.id, period.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        "param, value",
        [("date_start", date(2024, 1, 2)), ("date_end", date(2024, 1, 30)), ("status", PeriodStatus.CLOSED)],
    )
    def test_update_single_field_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (Wallet owner) by
        PATCH with valid data.
        THEN: Period updated in database.
        """
        api_client.force_authenticate(base_user)
        period = period_factory(
            wallet=wallet_factory(members=[base_user]),
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 31),
            status=PeriodStatus.ACTIVE,
        )
        payload = {param: value}
        url = period_detail_url(period.wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        assert getattr(period, param) == payload[param]

    @pytest.mark.parametrize(
        "param, value",
        [("date_start", date(2024, 1, 2)), ("date_end", date(2024, 1, 30)), ("status", PeriodStatus.CLOSED)],
    )
    def test_update_single_field_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (Wallet member) by
        PATCH with valid data.
        THEN: Period updated in database.
        """
        api_client.force_authenticate(base_user)
        period = period_factory(
            wallet=wallet_factory(members=[base_user]),
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 31),
            status=PeriodStatus.ACTIVE,
        )
        payload = {param: value}
        url = period_detail_url(period.wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        assert getattr(period, param) == payload[param]

    def test_update_many_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (Wallet member) by
        PATCH with valid data.
        THEN: Period updated in database.
        """
        api_client.force_authenticate(base_user)
        period = period_factory(
            wallet=wallet_factory(members=[base_user]),
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 31),
            status=PeriodStatus.ACTIVE,
        )
        payload = {
            "name": "2023_07",
            "date_start": date(2023, 7, 1),
            "date_end": date(2023, 7, 31),
            "status": PeriodStatus.CLOSED,
        }
        url = period_detail_url(period.wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        for param, value in payload.items():
            assert getattr(period, param) == value

    @pytest.mark.parametrize(
        "param, value",
        [("date_start", date(2023, 12, 31)), ("date_end", date(2024, 2, 1)), ("status", PeriodStatus.ACTIVE)],
    )
    def test_error_on_period_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (Wallet owner) by
        PATCH with invalid data.
        THEN: Bad request HTTP 400 returned.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        period_factory(
            wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), status=PeriodStatus.ACTIVE
        )
        period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), status=PeriodStatus.DRAFT
        )
        old_value = getattr(period, param)
        payload = {param: value}
        url = period_detail_url(wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        assert getattr(period, param) == old_value

    def test_error_cannot_update_closed_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Closed Period for Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by POST
        to update Period with active status.
        THEN: Bad request 400 returned, not updated in database.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), status=PeriodStatus.CLOSED
        )
        payload = {"status": PeriodStatus.ACTIVE}
        url = period_detail_url(wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        assert getattr(period, "status") == PeriodStatus.CLOSED

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data["detail"]
        assert response.data["detail"]["status"][0] == "Closed period cannot be changed."

    def test_error_active_period_cannot_be_moved_back_to_draft(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Active Period for Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by PATCH
        to update Period with draft status.
        THEN: Bad request 400 returned, not updated in database.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), status=PeriodStatus.ACTIVE
        )
        payload = {"status": PeriodStatus.DRAFT}
        url = period_detail_url(wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        assert getattr(period, "status") == PeriodStatus.ACTIVE

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data["detail"]
        assert response.data["detail"]["status"][0] == "Active period cannot be moved back to Draft status."

    def test_error_draft_period_cannot_be_closed(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Draft Period for Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by PATCH
        to update Period with closed status.
        THEN: Bad request 400 returned, not updated in database.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), status=PeriodStatus.DRAFT
        )
        payload = {"status": PeriodStatus.CLOSED}
        url = period_detail_url(wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        assert getattr(period, "status") == PeriodStatus.DRAFT

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data["detail"]
        assert response.data["detail"]["status"][0] == "Draft period cannot be closed. It has to be active first."

    def test_error_on_activating_period_when_other_active_exists(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Draft Period for Wallet in database created.
        WHEN: PeriodViewSet list view called for Wallet by authenticated User by PATCH
        to update Period with closed status.
        THEN: Bad request 400 returned, not updated in database.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        period_factory(
            wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), status=PeriodStatus.ACTIVE
        )
        period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), status=PeriodStatus.DRAFT
        )
        payload = {"status": PeriodStatus.ACTIVE}
        url = period_detail_url(wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        assert getattr(period, "status") == PeriodStatus.DRAFT

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data["detail"]
        assert response.data["detail"]["status"][0] == "🟢 Active period already exists in Wallet."

    def test_update_predictions_initial_plan_on_period_activating(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period and two ExpensePrediction for it created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User by
        PATCH to change period status to ACTIVE.
        THEN: Period updated in database, initial_value for both ExpensePredictions set.
        """
        api_client.force_authenticate(base_user)
        period = period_factory(
            wallet=wallet_factory(members=[base_user]),
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 31),
            status=PeriodStatus.DRAFT,
        )
        prediction_1 = expense_prediction_factory(period=period, current_plan=123.00)
        prediction_2 = expense_prediction_factory(period=period, current_plan=321.00)
        payload = {"status": PeriodStatus.ACTIVE}
        url = period_detail_url(period.wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        assert period.status == PeriodStatus.ACTIVE
        for prediction in (prediction_1, prediction_2):
            prediction.refresh_from_db()
            assert prediction.initial_plan == prediction.current_plan

    def test_create_zero_predictions_for_unpredicted_categories_on_activation(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with one ExpensePrediction and two expense categories created in database.
        WHEN: PeriodViewSet detail view called to activate period.
        THEN: ExpensePrediction with zero value created for unpredicted category.
        """
        from predictions.models import ExpensePrediction

        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        period = period_factory(
            wallet=wallet,
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 31),
            status=PeriodStatus.DRAFT,
        )
        category_1 = transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE)
        category_2 = transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE)
        expense_prediction_factory(period=period, category=category_1, current_plan=100.00)

        payload = {"status": PeriodStatus.ACTIVE}
        url = period_detail_url(period.wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        predictions = ExpensePrediction.objects.filter(period=period)
        assert predictions.count() == 2
        zero_prediction = predictions.filter(category=category_2).first()
        assert zero_prediction is not None
        assert zero_prediction.initial_plan == Decimal("0.00")
        assert zero_prediction.current_plan == Decimal("0.00")

    def test_error_update_period_for_not_accessible_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called by authenticated User (not Wallet owner nor member).
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        wallet = wallet_factory(members=[other_user])
        period = period_factory(wallet=wallet, status=PeriodStatus.DRAFT)
        api_client.force_authenticate(base_user)
        payload = {"name": "Updated Name"}
        url = period_detail_url(wallet.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        period.refresh_from_db()
        assert period.name != "Updated Name"


@pytest.mark.django_db
class TestPeriodViewSetDelete:
    """Tests for delete Period via PeriodViewSet."""

    def test_auth_required(self, period: Period, api_client: APIClient):
        """
        GIVEN: Period model instance in database created.
        WHEN: PeriodViewSet detail view called with DELETE without authentication.
        THEN: Unauthorized HTTP 401 status returned.
        """
        url = period_detail_url(period.wallet.id, period.id)

        res = api_client.delete(url)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: PeriodViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        url = period_detail_url(wallet.id, period.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_period_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (Wallet owner)
        by DELETE.
        THEN: Period deleted from database.
        """
        api_client.force_authenticate(base_user)
        period = period_factory(wallet=wallet_factory(members=[base_user]))
        url = period_detail_url(period.wallet.id, period.id)

        assert Period.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Period.objects.all().exists()

    def test_delete_period_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (Wallet member)
        by DELETE.
        THEN: Period deleted from database.
        """
        api_client.force_authenticate(base_user)
        period = period_factory(wallet=wallet_factory(members=[base_user]))
        url = period_detail_url(period.wallet.id, period.id)

        assert Period.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Period.objects.all().exists()

    def test_error_delete_not_accessible_period(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period created in database.
        WHEN: PeriodViewSet detail view called for Period by authenticated User (not Wallet owner
        nor member) by DELETE.
        THEN: Forbidden HTTP 403 returned, Period not deleted.
        """
        period = period_factory(wallet=wallet_factory(members=[user_factory()]))
        url = period_detail_url(period.wallet.id, period.id)
        api_client.force_authenticate(user_factory())

        assert Period.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Period.objects.filter(id=period.id).exists()
