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


def top_entities_chart_url(wallet_id: int) -> str:
    """Create and return a top entities in period chart URL."""
    return reverse("charts:top-entities-in-period-chart", args=[wallet_id])


@pytest.mark.django_db
class TestTopEntitiesInPeriodChartAPIView:
    """Tests for TopEntitiesInPeriodChartAPIView."""

    def test_auth_required(self, api_client: APIClient, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet instance in database.
        WHEN: TopEntitiesInPeriodChartAPIView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory()

        response = api_client.get(top_entities_chart_url(wallet.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TopEntitiesInPeriodChartAPIView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        url = top_entities_chart_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)

        response = api_client.get(
            url,
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
            HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}",
        )

        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance in database.
        WHEN: TopEntitiesInPeriodChartAPIView called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory()
        period = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_missing_required_parameters(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database.
        WHEN: TopEntitiesInPeriodChartAPIView called without required parameters.
        THEN: HTTP 200 - Response with empty xAxis and series arrays.
        """
        wallet = wallet_factory(owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.get(top_entities_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_missing_period_parameter(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database.
        WHEN: TopEntitiesInPeriodChartAPIView called without period parameter.
        THEN: HTTP 200 - Response with empty arrays.
        """
        wallet = wallet_factory(owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.get(top_entities_chart_url(wallet.id), {"transfer_type": str(CategoryType.EXPENSE.value)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_missing_transfer_type_parameter(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period in database.
        WHEN: TopEntitiesInPeriodChartAPIView called without transfer_type parameter.
        THEN: HTTP 200 - Response with empty arrays.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(top_entities_chart_url(wallet.id), {"period": str(period.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_chart_data_no_entities(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period but no entities in database.
        WHEN: TopEntitiesInPeriodChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet, name="Jan 2024")
        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_chart_data_entities_without_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period and entities but no transfers in database.
        WHEN: TopEntitiesInPeriodChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet, name="Jan 2024")
        entity_factory(wallet=wallet, name="Entity 1")
        entity_factory(wallet=wallet, name="Entity 2")
        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_chart_data_basic_scenario_expenses(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period, entities, and expense transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with transfer_type=EXPENSE.
        THEN: HTTP 200 - Response with top entities by expense amount.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity1 = entity_factory(wallet=wallet, name="Entity A")
        entity2 = entity_factory(wallet=wallet, name="Entity B")
        entity3 = entity_factory(wallet=wallet, name="Entity C")

        transfer_factory(
            period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("300.00"), deposit=deposit, entity=entity2
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("800.00"), deposit=deposit, entity=entity3
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Entity B", "Entity A", "Entity C"]
        assert response.data["series"] == [Decimal("300.00"), Decimal("500.00"), Decimal("800.00")]

    def test_get_chart_data_basic_scenario_incomes(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period, entities, and income transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with transfer_type=INCOME.
        THEN: HTTP 200 - Response with top entities by income amount.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        entity1 = entity_factory(wallet=wallet, name="Source A")
        entity2 = entity_factory(wallet=wallet, name="Source B")
        entity3 = entity_factory(wallet=wallet, name="Source C")

        transfer_factory(
            period=period, category=income_category, value=Decimal("1200.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=income_category, value=Decimal("900.00"), deposit=deposit, entity=entity2
        )
        transfer_factory(
            period=period, category=income_category, value=Decimal("1500.00"), deposit=deposit, entity=entity3
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.INCOME.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Source B", "Source A", "Source C"]
        assert response.data["series"] == [Decimal("900.00"), Decimal("1200.00"), Decimal("1500.00")]

    def test_entities_count_parameter_default(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with 8 entities with transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called without entities_count parameter.
        THEN: HTTP 200 - Response with top 5 entities (default).
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        for i in range(8):
            entity = entity_factory(wallet=wallet, name=f"Entity {i+1}")
            transfer_factory(
                period=period,
                category=expense_category,
                value=Decimal(f"{(i + 1) * 100}.00"),
                deposit=deposit,
                entity=entity,
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 5
        assert response.data["xAxis"] == ["Entity 4", "Entity 5", "Entity 6", "Entity 7", "Entity 8"]
        assert response.data["series"] == [
            Decimal("400.00"),
            Decimal("500.00"),
            Decimal("600.00"),
            Decimal("700.00"),
            Decimal("800.00"),
        ]

    def test_invalid_period_id(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period in database.
        WHEN: TopEntitiesInPeriodChartAPIView called with invalid period ID.
        THEN: HTTP 200 - Response with empty arrays.
        """
        wallet = wallet_factory(owner=base_user)
        period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": "99999", "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_deposit_filter_nonexistent_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entity transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with nonexistent deposit ID.
        THEN: HTTP 200 - Response with empty arrays (no matches).
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)
        entity = entity_factory(wallet=wallet, name="Entity 1")

        transfer_factory(
            period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit, entity=entity
        )

        api_client.force_authenticate(base_user)

        from entities.models import Deposit

        nonexistent_id = Deposit.objects.filter(wallet=wallet).order_by("-id").first().id + 1

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {
                "period": str(period.id),
                "transfer_type": str(CategoryType.EXPENSE.value),
                "deposit": str(nonexistent_id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_entities_count_zero(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entity transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with entities_count=0.
        THEN: HTTP 200 - Response with empty arrays.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)
        entity = entity_factory(wallet=wallet, name="Entity 1")

        transfer_factory(
            period=period, category=expense_category, value=Decimal("100.00"), deposit=deposit, entity=entity
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value), "entities_count": 0},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_entities_with_same_transfer_values_ordering(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple entities having same transfer amounts.
        WHEN: TopEntitiesInPeriodChartAPIView called.
        THEN: HTTP 200 - Response with entities ordered by transfer amount (ties handled by database).
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity1 = entity_factory(wallet=wallet, name="Entity A")
        entity2 = entity_factory(wallet=wallet, name="Entity B")
        entity3 = entity_factory(wallet=wallet, name="Entity C")

        # All entities have same transfer amount
        transfer_factory(
            period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit, entity=entity2
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit, entity=entity3
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        # All should have same value
        assert response.data["series"] == [Decimal("500.00"), Decimal("500.00"), Decimal("500.00")]

    def test_mixed_income_and_expense_filtered_correctly(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entity having both income and expense transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with transfer_type=EXPENSE.
        THEN: HTTP 200 - Response includes only expense transfers for the entity.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity = entity_factory(wallet=wallet, name="Mixed Entity")

        # Income transfers (should be ignored when filtering by EXPENSE)
        transfer_factory(
            period=period, category=income_category, value=Decimal("1000.00"), deposit=deposit, entity=entity
        )

        # Expense transfers (should be included)
        transfer_factory(
            period=period, category=expense_category, value=Decimal("200.00"), deposit=deposit, entity=entity
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("100.00"), deposit=deposit, entity=entity
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Mixed Entity"]
        assert response.data["series"] == [Decimal("300.00")]

    def test_entity_ordering_descending(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entities having different transfer amounts.
        WHEN: TopEntitiesInPeriodChartAPIView called.
        THEN: HTTP 200 - Response with entities ordered ascending (insert at 0).
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity1 = entity_factory(wallet=wallet, name="Low")
        entity2 = entity_factory(wallet=wallet, name="High")
        entity3 = entity_factory(wallet=wallet, name="Medium")

        transfer_factory(
            period=period, category=expense_category, value=Decimal("100.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("1000.00"), deposit=deposit, entity=entity2
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit, entity=entity3
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        # Due to insert(0, ...), lowest values appear first
        assert response.data["xAxis"] == ["Low", "Medium", "High"]
        assert response.data["series"] == [Decimal("100.00"), Decimal("500.00"), Decimal("1000.00")]

    def test_entities_count_parameter_custom_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with 8 entities with transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with entities_count=3.
        THEN: HTTP 200 - Response with top 3 entities.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        for i in range(8):
            entity = entity_factory(wallet=wallet, name=f"Entity {i}")
            transfer_factory(
                period=period,
                category=expense_category,
                value=Decimal(f"{(i + 1) * 100}.00"),
                deposit=deposit,
                entity=entity,
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value), "entities_count": 3},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["Entity 5", "Entity 6", "Entity 7"]
        assert response.data["series"] == [Decimal("600.00"), Decimal("700.00"), Decimal("800.00")]

    def test_entities_count_parameter_exceeds_available(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with 3 entities with transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with entities_count=10.
        THEN: HTTP 200 - Response with all 3 available entities.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity1 = entity_factory(wallet=wallet, name="Entity 1")
        entity2 = entity_factory(wallet=wallet, name="Entity 2")
        entity3 = entity_factory(wallet=wallet, name="Entity 3")

        transfer_factory(
            period=period, category=expense_category, value=Decimal("100.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("200.00"), deposit=deposit, entity=entity2
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("300.00"), deposit=deposit, entity=entity3
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value), "entities_count": 10},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["Entity 1", "Entity 2", "Entity 3"]

    def test_multiple_transfers_same_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entity having multiple transfers in same period.
        WHEN: TopEntitiesInPeriodChartAPIView called.
        THEN: HTTP 200 - Response with correctly summed values per entity.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity1 = entity_factory(wallet=wallet, name="Entity 1")
        entity2 = entity_factory(wallet=wallet, name="Entity 2")

        # Multiple transfers for entity1
        transfer_factory(
            period=period, category=expense_category, value=Decimal("100.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("200.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("50.50"), deposit=deposit, entity=entity1
        )

        # Single transfer for entity2
        transfer_factory(
            period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit, entity=entity2
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Entity 1", "Entity 2"]
        assert response.data["series"] == [Decimal("350.50"), Decimal("500.00")]

    def test_deposit_filter_single_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple deposits and entity transfers.
        WHEN: TopEntitiesInPeriodChartAPIView called with deposit filter.
        THEN: HTTP 200 - Response with data only from specified deposit.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)

        deposit1 = deposit_factory(wallet=wallet)
        deposit2 = deposit_factory(wallet=wallet)

        expense_category1 = transfer_category_factory(
            wallet=wallet, deposit=deposit1, category_type=CategoryType.EXPENSE
        )
        expense_category2 = transfer_category_factory(
            wallet=wallet, deposit=deposit2, category_type=CategoryType.EXPENSE
        )

        entity1 = entity_factory(wallet=wallet, name="Entity 1")
        entity2 = entity_factory(wallet=wallet, name="Entity 2")

        # Transfers for deposit1
        transfer_factory(
            period=period, category=expense_category1, value=Decimal("300.00"), deposit=deposit1, entity=entity1
        )

        # Transfers for deposit2
        transfer_factory(
            period=period, category=expense_category2, value=Decimal("700.00"), deposit=deposit2, entity=entity2
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {
                "period": str(period.id),
                "transfer_type": str(CategoryType.EXPENSE.value),
                "deposit": str(deposit1.id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Entity 1"]
        assert response.data["series"] == [Decimal("300.00")]

    def test_deposit_filter_aggregates_entity_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entity having transfers in multiple deposits.
        WHEN: TopEntitiesInPeriodChartAPIView called with deposit filter.
        THEN: HTTP 200 - Response with entity data only from specified deposit.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)

        deposit1 = deposit_factory(wallet=wallet)
        deposit2 = deposit_factory(wallet=wallet)

        expense_category1 = transfer_category_factory(
            wallet=wallet, deposit=deposit1, category_type=CategoryType.EXPENSE
        )
        expense_category2 = transfer_category_factory(
            wallet=wallet, deposit=deposit2, category_type=CategoryType.EXPENSE
        )

        entity = entity_factory(wallet=wallet, name="Entity 1")

        # Multiple transfers in deposit1
        transfer_factory(
            period=period, category=expense_category1, value=Decimal("100.00"), deposit=deposit1, entity=entity
        )
        transfer_factory(
            period=period, category=expense_category1, value=Decimal("200.00"), deposit=deposit1, entity=entity
        )

        # Transfer in deposit2 (should be excluded)
        transfer_factory(
            period=period, category=expense_category2, value=Decimal("500.00"), deposit=deposit2, entity=entity
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {
                "period": str(period.id),
                "transfer_type": str(CategoryType.EXPENSE.value),
                "deposit": str(deposit1.id),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Entity 1"]
        assert response.data["series"] == [Decimal("300.00")]

    def test_decimal_precision(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entity transfers containing decimal values.
        WHEN: TopEntitiesInPeriodChartAPIView called.
        THEN: HTTP 200 - Response with correct decimal precision.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity = entity_factory(wallet=wallet, name="Entity 1")

        transfer_factory(
            period=period, category=expense_category, value=Decimal("123.45"), deposit=deposit, entity=entity
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("67.89"), deposit=deposit, entity=entity
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["series"] == [Decimal("191.34")]

    def test_large_values(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entity transfers containing large monetary values.
        WHEN: TopEntitiesInPeriodChartAPIView called.
        THEN: HTTP 200 - Response with correct calculations for large values.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity = entity_factory(wallet=wallet, name="Big Spender")

        transfer_factory(
            period=period, category=expense_category, value=Decimal("999999.99"), deposit=deposit, entity=entity
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["series"] == [Decimal("999999.99")]

    def test_entities_with_zero_transfers_excluded(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with entities, some with transfers and some without.
        WHEN: TopEntitiesInPeriodChartAPIView called.
        THEN: HTTP 200 - Response only includes entities with transfers > 0.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        entity1 = entity_factory(wallet=wallet, name="Entity 1")
        entity2 = entity_factory(wallet=wallet, name="Entity 2")
        entity_factory(wallet=wallet, name="Entity 3")  # No transfers

        transfer_factory(
            period=period, category=expense_category, value=Decimal("100.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("200.00"), deposit=deposit, entity=entity2
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            top_entities_chart_url(wallet.id),
            {"period": str(period.id), "transfer_type": str(CategoryType.EXPENSE.value)},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["series"] == [Decimal("100.00"), Decimal("200.00")]
