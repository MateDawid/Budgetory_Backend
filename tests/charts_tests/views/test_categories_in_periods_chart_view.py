from datetime import date
from decimal import Decimal

import pytest
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from categories.models.choices.category_type import CategoryType
from charts.views.categories_in_periods_chart_view import get_categories_transfers_sums_in_period


def categories_results_url(wallet_id: int) -> str:
    """Create and return a categories results URL."""
    return reverse("charts:categories-in-periods-chart", args=[wallet_id])


@pytest.mark.django_db
class TestCategoriesInPeriodsChartAPIView:
    """Tests for CategoriesInPeriodsChartAPIView."""

    def test_auth_required(self, api_client: APIClient, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet instance in database.
        WHEN: CategoriesInPeriodsChartAPIView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory()

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: CategoriesInPeriodsChartAPIView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = categories_results_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)

        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")

        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance in database.
        WHEN: CategoriesInPeriodsChartAPIView called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_get_categories_results_empty_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with no periods and no categories in database.
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_categories_results_no_periods(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with categories but no periods in database.
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        transfer_category_factory(wallet=wallet, deposit=deposit)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_categories_results_no_categories(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods but no categories in database.
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_categories_results_basic_scenario(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods and categories but no transfers.
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with periods on xAxis and categories with zero values in series.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet, name="Jan 2024")
        period_factory(wallet=wallet, name="Feb 2024")
        deposit = deposit_factory(wallet=wallet, name="Checking Account")
        transfer_category_factory(wallet=wallet, deposit=deposit, name="Salary", category_type=CategoryType.INCOME)

        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert len(response.data["series"]) == 1
        assert response.data["series"][0]["label"] == "(Checking Account) Salary"
        assert response.data["series"][0]["data"] == [0.0, 0.0]
        assert "rgba(" in response.data["series"][0]["color"]

    def test_get_categories_results_with_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods, categories, and transfers.
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with correct transfer sum calculations per category per period.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(
            wallet=wallet, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = period_factory(
            wallet=wallet, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )
        period3 = period_factory(
            wallet=wallet, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31)
        )

        # Create deposits and categories
        deposit1 = deposit_factory(wallet=wallet, name="Checking")
        deposit2 = deposit_factory(wallet=wallet, name="Savings")

        salary_category = transfer_category_factory(
            wallet=wallet, deposit=deposit1, name="Salary", category_type=CategoryType.INCOME
        )
        groceries_category = transfer_category_factory(
            wallet=wallet, deposit=deposit1, name="Groceries", category_type=CategoryType.EXPENSE
        )
        interest_category = transfer_category_factory(
            wallet=wallet, deposit=deposit2, name="Interest", category_type=CategoryType.INCOME
        )

        # Transfers for Period 1
        transfer_factory(period=period1, category=salary_category, value=Decimal("3000.00"), deposit=deposit1)
        transfer_factory(period=period1, category=groceries_category, value=Decimal("500.00"), deposit=deposit1)
        transfer_factory(period=period1, category=interest_category, value=Decimal("50.00"), deposit=deposit2)

        # Transfers for Period 2
        transfer_factory(period=period2, category=salary_category, value=Decimal("3000.00"), deposit=deposit1)
        transfer_factory(period=period2, category=groceries_category, value=Decimal("600.00"), deposit=deposit1)
        transfer_factory(period=period2, category=interest_category, value=Decimal("55.00"), deposit=deposit2)

        # Transfers for Period 3
        transfer_factory(period=period3, category=salary_category, value=Decimal("3000.00"), deposit=deposit1)
        transfer_factory(period=period3, category=groceries_category, value=Decimal("450.00"), deposit=deposit1)
        transfer_factory(period=period3, category=interest_category, value=Decimal("60.00"), deposit=deposit2)

        api_client.force_authenticate(base_user)

        # Test without filtering - all categories and periods
        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]
        assert len(response.data["series"]) == 3

        # Find specific categories in response (sorted by deposit_name, category_type, priority, name)
        salary_series = next(s for s in response.data["series"] if s["label"] == "(Checking) Salary")
        groceries_series = next(s for s in response.data["series"] if s["label"] == "(Checking) Groceries")
        interest_series = next(s for s in response.data["series"] if s["label"] == "(Savings) Interest")

        # Verify calculations (non-cumulative, just period sums)
        assert salary_series["data"] == [3000.0, 3000.0, 3000.0]
        assert groceries_series["data"] == [500.0, 600.0, 450.0]
        assert interest_series["data"] == [50.0, 55.0, 60.0]

        # Test with period filtering
        response = api_client.get(
            categories_results_url(wallet.id), {"period_from": period2.id, "period_to": period3.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Feb 2024", "Mar 2024"]

        # Test with category_type filtering
        response = api_client.get(categories_results_url(wallet.id), {"category_type": CategoryType.INCOME})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 2  # Only income categories

        # Test with specific category filtering
        response = api_client.get(categories_results_url(wallet.id), {"category": salary_category.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 1
        assert response.data["series"][0]["label"] == "(Checking) Salary"

        # Test with deposit filtering
        response = api_client.get(categories_results_url(wallet.id), {"deposit": deposit1.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 2  # Only categories from deposit1

    def test_large_dataset_performance_simulation(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with many periods, categories, and transfers to simulate real-world load.
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response returned efficiently with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])

        # Create 12 periods (full year)
        periods = []
        for month in range(1, 13):
            period = period_factory(
                wallet=wallet,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )
            periods.append(period)

        # Create deposits and multiple categories
        deposit = deposit_factory(wallet=wallet, name="Main Account")

        categories = []
        for i in range(10):
            category = transfer_category_factory(
                wallet=wallet,
                deposit=deposit,
                name=f"Category {i + 1}",
                category_type=CategoryType.INCOME if i % 2 == 0 else CategoryType.EXPENSE,
            )
            categories.append(category)

        # Create transfers for each period and category combination
        for period in periods:
            for j, category in enumerate(categories):
                value = Decimal(str(100 + (j * 50)))
                transfer_factory(
                    period=period,
                    category=category,
                    value=value,
                    deposit=deposit,
                )

        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 12  # All 12 periods
        assert len(response.data["series"]) == 10  # All 10 categories

        # Verify that each category has data for all periods
        for series in response.data["series"]:
            assert len(series["data"]) == 12
            # Verify that all values are positive (they're absolute transfer sums)
            for value in series["data"]:
                assert value >= 0

    def test_edge_cases_and_error_handling(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with various edge cases (zero values, missing data).
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response handles edge cases gracefully with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(wallet=wallet, name="Period 1")
        period2 = period_factory(wallet=wallet, name="Period 2")

        deposit = deposit_factory(wallet=wallet, name="Account")

        # Categories with different scenarios
        transfer_category_factory(
            wallet=wallet, deposit=deposit, name="Zero Transfers", category_type=CategoryType.EXPENSE
        )
        normal_category = transfer_category_factory(
            wallet=wallet, deposit=deposit, name="Normal", category_type=CategoryType.INCOME
        )
        partial_category = transfer_category_factory(
            wallet=wallet, deposit=deposit, name="Partial", category_type=CategoryType.EXPENSE
        )

        # Zero category: no transactions
        # Partial category: only in period 1
        transfer_factory(period=period1, category=partial_category, value=Decimal("100.00"), deposit=deposit)

        # Normal category: transfers in both periods
        transfer_factory(period=period1, category=normal_category, value=Decimal("500.00"), deposit=deposit)
        transfer_factory(period=period2, category=normal_category, value=Decimal("600.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 3

        # Find each category's data
        zero_series = next(s for s in response.data["series"] if s["label"] == "(Account) Zero Transfers")
        normal_series = next(s for s in response.data["series"] if s["label"] == "(Account) Normal")
        partial_series = next(s for s in response.data["series"] if s["label"] == "(Account) Partial")

        # Verify calculations
        assert zero_series["data"] == [0.0, 0.0]  # No transactions
        assert normal_series["data"] == [500.0, 600.0]  # Transfers in both periods
        assert partial_series["data"] == [100.0, 0.0]  # Only in period 1

    def test_multiple_transfers_same_category_same_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple transfers for same category in same period.
        WHEN: CategoriesInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response aggregates all transfers for the category in that period.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet, name="Account")
        category = transfer_category_factory(
            wallet=wallet, deposit=deposit, name="Groceries", category_type=CategoryType.EXPENSE
        )

        # Multiple transfers same category, same period
        transfer_factory(period=period, category=category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("50.50"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("200.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(categories_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 1
        assert response.data["series"][0]["data"] == [350.5]  # Sum of all transfers

    def test_empty_period_no_transfers(
        self,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with no transfers for specified categories.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: Empty dict returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category.id],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {}

    def test_different_wallets_isolation(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple wallets with categories and transfers.
        WHEN: get_categories_transfers_sums_in_period called for specific wallet.
        THEN: Only transfers from specified wallet included.
        """
        wallet1 = wallet_factory(members=[base_user])
        wallet2 = wallet_factory(members=[base_user])

        period1 = period_factory(wallet=wallet1, name="Jan 2024")
        period2 = period_factory(wallet=wallet2, name="Jan 2024")

        deposit1 = deposit_factory(wallet=wallet1)
        deposit2 = deposit_factory(wallet=wallet2)

        category1 = transfer_category_factory(wallet=wallet1, deposit=deposit1, category_type=CategoryType.INCOME)
        category2 = transfer_category_factory(wallet=wallet2, deposit=deposit2, category_type=CategoryType.INCOME)

        transfer_factory(period=period1, category=category1, value=Decimal("100.00"), deposit=deposit1)
        transfer_factory(period=period2, category=category2, value=Decimal("200.00"), deposit=deposit2)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet1.id,
            categories_ids=[category1.id],
            period={"pk": period1.id, "name": period1.name},
        )

        assert result == {category1.id: 100.0}
        assert category2.id not in result

    def test_decimal_precision_handling(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Transfers with precise decimal values.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: Result maintains proper decimal precision as float.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=category, value=Decimal("100.33"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("200.67"), deposit=deposit)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category.id],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {category.id: 301.0}

    def test_large_number_of_transfers(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Category with many transfers in single period.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: All transfers correctly aggregated.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Create 50 transfers
        expected_sum = 0.0
        for i in range(50):
            value = Decimal(f"{(i + 1) * 10}.00")
            transfer_factory(period=period, category=category, value=value, deposit=deposit)
            expected_sum += float(value)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category.id],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {category.id: expected_sum}

    def test_empty_category_ids_list(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Empty list of category IDs.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: Empty dict returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {}

    def test_nonexistent_category_ids(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Non-existent category IDs.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: Empty dict returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[999999, 999998],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {} == {}

    def test_single_category_single_transfer(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Single category with one transfer in period.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: Dict with category_id and correct sum returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        transfer_factory(period=period, category=category, value=Decimal("500.00"), deposit=deposit)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category.id],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {category.id: 500.0}

    def test_multiple_transfers_same_category_aggregation(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple transfers for same category in period.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: Dict with category_id and aggregated sum returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("200.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("150.50"), deposit=deposit)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category.id],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {category.id: 450.5}

    def test_multiple_categories_same_period(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple categories with transfers in same period.
        WHEN: get_categories_transfers_sums_in_period called with all category IDs.
        THEN: Dict with all category_ids and their respective sums returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)

        category1 = transfer_category_factory(wallet=wallet, deposit=deposit, name="Cat 1")
        category2 = transfer_category_factory(wallet=wallet, deposit=deposit, name="Cat 2")
        category3 = transfer_category_factory(wallet=wallet, deposit=deposit, name="Cat 3")

        transfer_factory(period=period, category=category1, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period, category=category2, value=Decimal("200.00"), deposit=deposit)
        transfer_factory(period=period, category=category3, value=Decimal("300.00"), deposit=deposit)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category1.id, category2.id, category3.id],
            period={"pk": period.id, "name": period.name},
        )

        assert result == {category1.id: 100.0, category2.id: 200.0, category3.id: 300.0}

    def test_category_with_no_transfers_excluded(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple categories, some with transfers and some without.
        WHEN: get_categories_transfers_sums_in_period called.
        THEN: Only categories with transfers appear in result dict.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)

        category_with_transfer = transfer_category_factory(wallet=wallet, deposit=deposit, name="With Transfer")
        category_without_transfer = transfer_category_factory(wallet=wallet, deposit=deposit, name="Without Transfer")

        transfer_factory(period=period, category=category_with_transfer, value=Decimal("500.00"), deposit=deposit)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category_with_transfer.id, category_without_transfer.id],
            period={"pk": period.id, "name": period.name},
        )

        assert category_with_transfer.id in result
        assert category_without_transfer.id not in result
        assert result[category_with_transfer.id] == 500.0

    def test_different_periods_isolation(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Transfers in multiple periods for same category.
        WHEN: get_categories_transfers_sums_in_period called for specific period.
        THEN: Only transfers from specified period included in sum.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(wallet=wallet, name="Jan 2024")
        period2 = period_factory(wallet=wallet, name="Feb 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit)

        transfer_factory(period=period1, category=category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period2, category=category, value=Decimal("200.00"), deposit=deposit)

        result = get_categories_transfers_sums_in_period(
            wallet_pk=wallet.id,
            categories_ids=[category.id],
            period={"pk": period1.id, "name": period1.name},
        )

        assert result
