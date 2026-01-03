from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from predictions_tests.utils import annotate_expense_prediction_queryset
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from periods.models.choices.period_status import PeriodStatus
from predictions.models.expense_prediction_model import ExpensePrediction
from predictions.serializers.expense_prediction_serializer import ExpensePredictionSerializer


def expense_prediction_url(wallet_id: int):
    """Create and return an ExpensePrediction list URL."""
    return reverse("wallets:expense_prediction-list", args=[wallet_id])


def expense_prediction_detail_url(wallet_id: int, prediction_id: int):
    """Create and return an ExpensePrediction detail URL."""
    return reverse("wallets:expense_prediction-detail", args=[wallet_id, prediction_id])


@pytest.mark.django_db
class TestExpensePredictionViewSetList:
    """Tests for list view on ExpensePredictionViewSet."""

    def test_auth_required(self, api_client: APIClient, expense_prediction: ExpensePrediction):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(expense_prediction_url(expense_prediction.period.wallet.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = expense_prediction_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten ExpensePrediction model instances for single Wallet created in database.
        WHEN: ExpensePredictionViewSet called by Wallet member without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        wallet = wallet_factory(members=[base_user])
        for _ in range(10):
            expense_prediction_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 10

    def test_get_response_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten ExpensePrediction model instances for single Wallet created in database.
        WHEN: ExpensePredictionViewSet called by Wallet member with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        wallet = wallet_factory(members=[base_user])
        for _ in range(10):
            expense_prediction_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        expense_prediction = expense_prediction_factory()

        api_client.force_authenticate(other_user)

        response = api_client.get(expense_prediction_url(expense_prediction.period.wallet.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_retrieve_prediction_list_by_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction model instances for single Wallet created in database.
        WHEN: ExpensePredictionViewSet called by Wallet member.
        THEN: Response with serialized Wallet ExpensePrediction list returned.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        expense_prediction_factory(
            wallet=wallet,
            category=transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE),
        )
        expense_prediction_factory(
            wallet=wallet,
            category=transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE),
        )

        response = api_client.get(expense_prediction_url(wallet.id))

        predictions = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet=wallet)
        ).order_by("id")
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data
        for prediction in serializer.data:
            category = TransferCategory.objects.get(id=prediction["category"])
            assert prediction["category_display"] == f"📉{category.name}"
            assert prediction["category_priority"] == CategoryPriority(category.priority).label
            assert prediction["category_deposit"] == getattr(category.deposit, "name", None)

    def test_prediction_list_limited_to_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction model instances for different Wallets created in database.
        WHEN: ExpensePredictionViewSet called by one of Wallets owner.
        THEN: Response with serialized ExpensePrediction list (only from given Wallet) returned.
        """
        wallet = wallet_factory(members=[base_user])
        prediction = expense_prediction_factory(wallet=wallet)
        expense_prediction_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id))

        predictions = annotate_expense_prediction_queryset(ExpensePrediction.objects.filter(period__wallet=wallet))
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id

    def test_previous_plan_field_in_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction model instances for consecutive Periods in database.
        WHEN: ExpensePredictionViewSet called by one of Wallets owner.
        THEN: Response with serialized ExpensePrediction list containing calculated "previous_plan" field returned.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        category = transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE)
        previous_period = period_factory(wallet=wallet, date_start=date(2025, 6, 1), date_end=date(2025, 6, 30))
        current_period = period_factory(wallet=wallet, date_start=date(2025, 7, 1), date_end=date(2025, 7, 31))
        previous_prediction = expense_prediction_factory(
            wallet=wallet, period=previous_period, category=category, current_plan=Decimal("100.00")
        )
        current_prediction = expense_prediction_factory(
            wallet=wallet, period=current_period, category=category, current_plan=Decimal("200.00")
        )

        response = api_client.get(expense_prediction_url(wallet.id))

        predictions = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet=wallet)
        ).order_by("id")
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data
        assert serializer.data[0]["id"] == previous_prediction.id and serializer.data[0]["previous_plan"] == str(
            Decimal(Decimal("0.00")).quantize(Decimal("0.00"))
        )
        assert serializer.data[1]["id"] == current_prediction.id and serializer.data[1]["previous_plan"] == str(
            Decimal(Decimal("100.00")).quantize(Decimal("0.00"))
        )

    def test_current_result_and_previous_result_field_in_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction model instances for consecutive Periods in database.
        Six Transfers (two matching current period, two matching previous period, two others) created too.
        WHEN: ExpensePredictionViewSet called by one of Wallets owner.
        THEN: Response with serialized ExpensePrediction list containing calculated "current_result"
        and "previous_result" field returned.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)
        previous_period = period_factory(wallet=wallet, date_start=date(2025, 6, 1), date_end=date(2025, 6, 30))
        current_period = period_factory(wallet=wallet, date_start=date(2025, 7, 1), date_end=date(2025, 7, 31))
        previous_prediction = expense_prediction_factory(
            wallet=wallet, deposit=deposit, period=previous_period, category=category
        )
        current_prediction = expense_prediction_factory(
            wallet=wallet, deposit=deposit, period=current_period, category=category
        )
        # Transfer matching previous ExpensePrediction
        expense_factory(
            wallet=wallet, deposit=deposit, category=category, period=previous_period, value=Decimal("1.00")
        )
        expense_factory(
            wallet=wallet, deposit=deposit, category=category, period=previous_period, value=Decimal("2.00")
        )
        # Transfer matching current ExpensePrediction
        expense_factory(
            wallet=wallet, deposit=deposit, category=category, period=current_period, value=Decimal("10.00")
        )
        expense_factory(
            wallet=wallet, deposit=deposit, category=category, period=current_period, value=Decimal("20.00")
        )
        # Other Transfers
        expense_factory(wallet=wallet, deposit=deposit, value=Decimal("100.00"))
        expense_factory(wallet=wallet, deposit=deposit, value=Decimal("200.00"))

        response = api_client.get(expense_prediction_url(wallet.id))

        predictions = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet=wallet)
        ).order_by("id")
        serializer = ExpensePredictionSerializer(predictions, many=True)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data
        assert serializer.data[0]["id"] == previous_prediction.id and serializer.data[0]["previous_result"] == str(
            Decimal(Decimal("0.00")).quantize(Decimal("0.00"))
        )
        assert serializer.data[0]["id"] == previous_prediction.id and serializer.data[0]["current_result"] == str(
            Decimal(Decimal("3.00")).quantize(Decimal("0.00"))
        )
        assert serializer.data[1]["id"] == current_prediction.id and serializer.data[1]["previous_result"] == str(
            Decimal(Decimal("3.00")).quantize(Decimal("0.00"))
        )
        assert serializer.data[1]["id"] == current_prediction.id and serializer.data[1]["current_result"] == str(
            Decimal(Decimal("30.00")).quantize(Decimal("0.00"))
        )


@pytest.mark.django_db
class TestExpensePredictionViewSetCreate:
    """Tests for create ExpensePrediction on ExpensePredictionViewSet."""

    PAYLOAD = {
        "current_plan": Decimal("100.00"),
        "description": "Expense prediction.",
    }

    def test_auth_required(self, api_client: APIClient, expense_prediction: ExpensePrediction):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        url = expense_prediction_url(expense_prediction.period.wallet.id)
        response = api_client.post(url, data={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet list endpoint called with POST.
        THEN: HTTP 400 returned - access granted, but input invalid.
        """
        wallet = wallet_factory(members=[base_user])
        url = expense_prediction_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet, Period and TransferCategory instances created in database. Valid payload
        for ExpensePrediction.
        WHEN: ExpensePredictionViewSet called with POST by User not belonging to Wallet with valid payload.
        THEN: Forbidden HTTP 403 returned. Object not created.
        """
        wallet = wallet_factory()
        payload = self.PAYLOAD.copy()
        api_client.force_authenticate(base_user)

        response = api_client.post(expense_prediction_url(wallet.id), payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."
        assert not ExpensePrediction.objects.filter(period__wallet=wallet).exists()

    def test_create_single_prediction(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet, Period and TransferCategory instances created in database. Valid payload prepared
        for ExpensePrediction.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Wallet with valid payload.
        THEN: ExpensePrediction object created in database with given payload
        """
        other_user = user_factory()
        wallet = wallet_factory(members=[base_user, other_user])
        deposit = deposit_factory(wallet=wallet)
        period = period_factory(wallet=wallet, status=PeriodStatus.DRAFT)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id
        payload["deposit"] = deposit.id
        api_client.force_authenticate(base_user)

        response = api_client.post(expense_prediction_url(wallet.id), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert ExpensePrediction.objects.filter(period__wallet=wallet).count() == 1
        prediction = ExpensePrediction.objects.get(id=response.data["id"])
        for key in self.PAYLOAD:
            assert getattr(prediction, key) == self.PAYLOAD[key]
        assert getattr(prediction, "initial_plan") is None
        assert prediction.category == category
        assert prediction.period == period
        assert prediction.deposit == deposit
        serializer = ExpensePredictionSerializer(prediction)
        assert response.data == serializer.data

    @pytest.mark.parametrize("current_plan", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_lower_than_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        current_plan: Decimal,
    ):
        """
        GIVEN: Wallet, Period and TransferCategory instances created in database. Payload for ExpensePrediction
        with current_plan too low.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id
        payload["current_plan"] = current_plan

        response = api_client.post(expense_prediction_url(wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "current_plan" in response.data["detail"]
        assert response.data["detail"]["current_plan"][0] == "Value should be higher than 0.00."
        assert not ExpensePrediction.objects.filter(period__wallet=wallet).exists()

    def test_error_category_not_with_expense_type(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet, Period and TransferCategory instances created in database. Payload for ExpensePrediction
        with INCOME TransferCategory as category.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, category_type=CategoryType.INCOME)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id

        response = api_client.post(expense_prediction_url(wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "Incorrect category provided. Please provide expense category."
        assert not ExpensePrediction.objects.filter(period__wallet=wallet).exists()

    def test_error_add_prediction_to_closed_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet, Period and TransferCategory instances created in database. Payload for ExpensePrediction
        with CLOSED Period as period.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, status=PeriodStatus.CLOSED)
        category = transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id

        response = api_client.post(expense_prediction_url(wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data["detail"]
        assert response.data["detail"]["period"][0] == "New Expense Prediction cannot be added to closed Period."
        assert not ExpensePrediction.objects.filter(period__wallet=wallet).exists()

    def test_error_add_prediction_to_active_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet, Period and TransferCategory instances created in database. Payload for ExpensePrediction
        with ACTIVE Period as period.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, status=PeriodStatus.ACTIVE)
        category = transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id

        response = api_client.post(expense_prediction_url(wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data["detail"]
        assert response.data["detail"]["period"][0] == "New Expense Prediction cannot be added to active Period."
        assert not ExpensePrediction.objects.filter(period__wallet=wallet).exists()


@pytest.mark.django_db
class TestExpensePredictionViewSetDetail:
    """Tests for detail view on ExpensePredictionViewSet."""

    def test_auth_required(self, api_client: APIClient, expense_prediction: ExpensePrediction):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet detail method called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(
            expense_prediction_detail_url(expense_prediction.period.wallet.id, expense_prediction.id)
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        expense_prediction = expense_prediction_factory(wallet=wallet)
        url = expense_prediction_detail_url(expense_prediction.period.wallet.id, expense_prediction.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet detail method called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        expense_prediction = expense_prediction_factory()
        api_client.force_authenticate(other_user)

        response = api_client.get(
            expense_prediction_detail_url(expense_prediction.period.wallet.id, expense_prediction.id)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    @pytest.mark.parametrize("user_type", ["owner", "member"])
    def test_get_prediction_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        user_type: str,
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called by User belonging to Wallet.
        THEN: HTTP 200, ExpensePrediction details returned.
        """
        if user_type == "owner":
            wallet = wallet_factory(members=[base_user])
        else:
            wallet = wallet_factory(members=[base_user])
        prediction = expense_prediction_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(wallet.id, prediction.id)

        response = api_client.get(url)
        serializer = ExpensePredictionSerializer(
            annotate_expense_prediction_queryset(ExpensePrediction.objects.filter(id=prediction.id)).first()
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_prediction_details_unauthenticated(
        self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called without authentication.
        THEN: Unauthorized HTTP 401.
        """
        prediction = expense_prediction_factory()
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_details_from_not_accessible_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        prediction = expense_prediction_factory(wallet=wallet_factory())
        api_client.force_authenticate(base_user)

        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."


@pytest.mark.django_db
class TestExpensePredictionViewSetUpdate:
    """Tests for update view on ExpensePredictionViewSet."""

    PAYLOAD = {
        "current_plan": Decimal("100.00"),
        "description": "Expense prediction.",
    }

    def test_auth_required(
        self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401.
        """
        prediction = expense_prediction_factory()
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.patch(url, {})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        expense_prediction = expense_prediction_factory(wallet=wallet)
        url = expense_prediction_detail_url(expense_prediction.period.wallet.id, expense_prediction.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called with PATCH by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        prediction = expense_prediction_factory(wallet=wallet_factory())
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.patch(url, {})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    @pytest.mark.parametrize(
        "param, value",
        [
            ("current_plan", Decimal("200.00")),
            ("description", "New description"),
        ],
    )
    @pytest.mark.django_db
    def test_prediction_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called with PATCH by User belonging to Wallet.
        THEN: HTTP 200, ExpensePrediction updated.
        """
        wallet = wallet_factory(members=[base_user])
        prediction = expense_prediction_factory(wallet=wallet, **self.PAYLOAD)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(wallet.id, prediction.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        prediction.refresh_from_db()
        assert getattr(prediction, param) == update_payload[param]

    def test_prediction_update_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database. Update payload with "category" value prepared.
        WHEN: ExpensePredictionViewSet detail view called with PATCH by User belonging to Wallet with valid payload.
        THEN: HTTP 200, Deposit updated with "category" value.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)
        prediction = expense_prediction_factory(wallet=wallet, deposit=deposit, **self.PAYLOAD)
        update_payload = {"category": category.id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(wallet.id, prediction.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        prediction.refresh_from_db()
        assert prediction.category == category

    def test_error_update_category_does_not_belong_to_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance created in database. TransferCategory not belonging to Wallet as
        'category' in payload.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        wallet = wallet_factory(members=[base_user])
        prediction = expense_prediction_factory(wallet=wallet)
        payload = {"category": transfer_category_factory(category_type=CategoryType.EXPENSE).id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0] == "Wallet for period and category fields is not the same."
        )

    def test_error_category_not_with_expense_type(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance created in database. INCOME TransferCategory as 'category' in payload.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        wallet = wallet_factory(members=[base_user])
        prediction = expense_prediction_factory(wallet=wallet)
        payload = {"category": transfer_category_factory(wallet=wallet, category_type=CategoryType.INCOME).id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "Incorrect category provided. Please provide expense category."

    def test_error_change_prediction_for_closed_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance created in database.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Wallet with valid payload, but when
        the Period of prediction is CLOSED.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, status=PeriodStatus.DRAFT)
        prediction = expense_prediction_factory(period=period)
        period.status = PeriodStatus.CLOSED
        period.save()
        payload = {"current_plan": Decimal("123.45")}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Expense Prediction cannot be changed when Period is closed."
        )

    def test_update_prediction_for_active_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance created in database.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Wallet with valid payload, but when
        the Period of prediction is ACTIVE.
        THEN: HTTP 200 returned. ExpensePrediction updated.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, status=PeriodStatus.DRAFT)
        prediction = expense_prediction_factory(period=period, current_plan=Decimal("100.00"))
        period.status = PeriodStatus.ACTIVE
        period.save()
        payload = {"current_plan": Decimal("123.45")}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        prediction.refresh_from_db()
        assert prediction.current_plan == Decimal("123.45")

    def test_error_change_period_of_prediction(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance created in database.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Wallet with other Period
        in payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet)
        prediction = expense_prediction_factory(period=period)
        payload = {"period": period_factory(wallet=wallet).id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data["detail"]
        assert response.data["detail"]["period"][0] == "Period for Expense Prediction cannot be changed."


@pytest.mark.django_db
class TestExpensePredictionViewSetDelete:
    """Tests for delete ExpensePrediction on ExpensePredictionViewSet."""

    def test_auth_required(
        self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called with DELETE without authentication.
        THEN: Unauthorized HTTP 401.
        """
        prediction = expense_prediction_factory()
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        wallet = wallet_factory(members=[base_user])
        expense_prediction = expense_prediction_factory(wallet=wallet)
        url = expense_prediction_detail_url(expense_prediction.period.wallet.id, expense_prediction.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called with DELETE by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        prediction = expense_prediction_factory(wallet=wallet_factory())
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.wallet.id, prediction.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_delete_prediction(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Wallet created in database.
        WHEN: ExpensePredictionViewSet detail view called with DELETE by User belonging to Wallet.
        THEN: No content HTTP 204, ExpensePrediction deleted.
        """
        wallet = wallet_factory(members=[base_user])
        prediction = expense_prediction_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(wallet.id, prediction.id)

        assert ExpensePrediction.objects.filter(period__wallet=wallet).count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ExpensePrediction.objects.filter(period__wallet=wallet).exists()
