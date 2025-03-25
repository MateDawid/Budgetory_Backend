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
from budgets.models.choices.period_status import PeriodStatus
from categories.models.choices.category_type import CategoryType
from predictions.models.expense_prediction_model import ExpensePrediction
from predictions.serializers.expense_prediction_serializer import ExpensePredictionSerializer


def expense_prediction_url(budget_id: int):
    """Create and return an ExpensePrediction list URL."""
    return reverse("budgets:expense_prediction-list", args=[budget_id])


def expense_prediction_detail_url(budget_id: int, prediction_id: int):
    """Create and return an ExpensePrediction detail URL."""
    return reverse("budgets:expense_prediction-detail", args=[budget_id, prediction_id])


@pytest.mark.django_db
class TestExpensePredictionViewSetList:
    """Tests for list view on ExpensePredictionViewSet."""

    def test_auth_required(self, api_client: APIClient, expense_prediction: ExpensePrediction):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(expense_prediction_url(expense_prediction.period.budget.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        url = expense_prediction_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        expense_prediction = expense_prediction_factory()

        api_client.force_authenticate(other_user)

        response = api_client.get(expense_prediction_url(expense_prediction.period.budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_retrieve_prediction_list_by_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction model instances for single Budget created in database.
        WHEN: ExpensePredictionViewSet called by Budget member.
        THEN: Response with serialized Budget ExpensePrediction list returned.
        """
        api_client.force_authenticate(base_user)
        budget = budget_factory(members=[base_user])
        for _ in range(2):
            expense_prediction_factory(budget=budget)

        response = api_client.get(expense_prediction_url(budget.id))

        predictions = ExpensePrediction.objects.filter(period__budget=budget)
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == serializer.data

    def test_prediction_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction model instances for different Budgets created in database.
        WHEN: ExpensePredictionViewSet called by one of Budgets owner.
        THEN: Response with serialized ExpensePrediction list (only from given Budget) returned.
        """
        budget = budget_factory(members=[base_user])
        prediction = expense_prediction_factory(budget=budget)
        expense_prediction_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id))

        predictions = ExpensePrediction.objects.filter(period__budget=budget)
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == predictions.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == prediction.id


@pytest.mark.django_db
class TestExpensePredictionViewSetCreate:
    """Tests for create ExpensePrediction on ExpensePredictionViewSet."""

    PAYLOAD = {
        "current_value": Decimal("100.00"),
        "description": "Expense prediction.",
    }

    def test_auth_required(self, api_client: APIClient, expense_prediction: ExpensePrediction):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        url = expense_prediction_url(expense_prediction.period.budget.id)
        response = api_client.post(url, data={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet list endpoint called with POST.
        THEN: HTTP 400 returned - access granted, but input invalid.
        """
        budget = budget_factory(members=[base_user])
        url = expense_prediction_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget, BudgetingPeriod and TransferCategory instances created in database. Valid payload
        for ExpensePrediction.
        WHEN: ExpensePredictionViewSet called with POST by User not belonging to Budget with valid payload.
        THEN: Forbidden HTTP 403 returned. Object not created.
        """
        budget = budget_factory()
        payload = self.PAYLOAD.copy()
        api_client.force_authenticate(base_user)

        response = api_client.post(expense_prediction_url(budget.id), payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."
        assert not ExpensePrediction.objects.filter(period__budget=budget).exists()

    def test_create_single_prediction(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget, BudgetingPeriod and TransferCategory instances created in database. Valid payload prepared
        for ExpensePrediction.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with valid payload.
        THEN: ExpensePrediction object created in database with given payload
        """
        other_user = user_factory()
        budget = budget_factory(members=[base_user, other_user])
        period = budgeting_period_factory(budget=budget, status=PeriodStatus.DRAFT)
        category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id
        api_client.force_authenticate(base_user)

        response = api_client.post(expense_prediction_url(budget.id), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert ExpensePrediction.objects.filter(period__budget=budget).count() == 1
        prediction = ExpensePrediction.objects.get(id=response.data["id"])
        for key in self.PAYLOAD:
            assert getattr(prediction, key) == self.PAYLOAD[key]
        assert getattr(prediction, "initial_value") is None
        assert prediction.category == category
        assert prediction.period == period
        serializer = ExpensePredictionSerializer(prediction)
        assert response.data == serializer.data

    def test_error_description_too_long(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget, BudgetingPeriod and TransferCategory instances created in database. Payload for ExpensePrediction
        with field value too long.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        max_length = ExpensePrediction._meta.get_field("description").max_length
        payload = self.PAYLOAD.copy()
        payload["description"] = (max_length + 1) * "a"

        response = api_client.post(expense_prediction_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "description" in response.data["detail"]
        assert (
            response.data["detail"]["description"][0] == f"Ensure this field has no more than {max_length} characters."
        )
        assert not ExpensePrediction.objects.filter(period__budget=budget).exists()

    @pytest.mark.parametrize("current_value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_lower_than_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        current_value: Decimal,
    ):
        """
        GIVEN: Budget, BudgetingPeriod and TransferCategory instances created in database. Payload for ExpensePrediction
        with current_value too low.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id
        payload["current_value"] = current_value

        response = api_client.post(expense_prediction_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "current_value" in response.data["detail"]
        assert response.data["detail"]["current_value"][0] == "Value should be higher than 0.00."
        assert not ExpensePrediction.objects.filter(period__budget=budget).exists()

    def test_error_category_not_with_expense_type(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget, BudgetingPeriod and TransferCategory instances created in database. Payload for ExpensePrediction
        with INCOME TransferCategory as category.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        category = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id

        response = api_client.post(expense_prediction_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "Incorrect category provided. Please provide expense category."
        assert not ExpensePrediction.objects.filter(period__budget=budget).exists()

    def test_error_add_prediction_to_closed_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget, BudgetingPeriod and TransferCategory instances created in database. Payload for ExpensePrediction
        with CLOSED BudgetingPeriod as period.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, status=PeriodStatus.CLOSED)
        category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id

        response = api_client.post(expense_prediction_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data["detail"]
        assert (
            response.data["detail"]["period"][0] == "New Expense Prediction cannot be added to closed Budgeting Period."
        )
        assert not ExpensePrediction.objects.filter(period__budget=budget).exists()

    def test_error_add_prediction_to_active_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget, BudgetingPeriod and TransferCategory instances created in database. Payload for ExpensePrediction
        with ACTIVE BudgetingPeriod as period.
        WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, status=PeriodStatus.ACTIVE)
        category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["period"] = period.id
        payload["category"] = category.id

        response = api_client.post(expense_prediction_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data["detail"]
        assert (
            response.data["detail"]["period"][0] == "New Expense Prediction cannot be added to active Budgeting Period."
        )
        assert not ExpensePrediction.objects.filter(period__budget=budget).exists()

    # TODO: Update prediction for CLOSED period
    # TODO: Update prediction for ACTIVE period
    # TODO: Coverage check


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
            expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        expense_prediction = expense_prediction_factory(budget=budget)
        url = expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet detail method called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        expense_prediction = expense_prediction_factory()
        api_client.force_authenticate(other_user)

        response = api_client.get(
            expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize("user_type", ["owner", "member"])
    def test_get_prediction_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        user_type: str,
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, ExpensePrediction details returned.
        """
        if user_type == "owner":
            budget = budget_factory(members=[base_user])
        else:
            budget = budget_factory(members=[base_user])
        prediction = expense_prediction_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(budget.id, prediction.id)

        response = api_client.get(url)
        serializer = ExpensePredictionSerializer(prediction)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_prediction_details_unauthenticated(
        self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called without authentication.
        THEN: Unauthorized HTTP 401.
        """
        prediction = expense_prediction_factory()
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_details_from_not_accessible_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        prediction = expense_prediction_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)

        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."


@pytest.mark.django_db
class TestExpensePredictionViewSetUpdate:
    """Tests for update view on ExpensePredictionViewSet."""

    PAYLOAD = {
        "current_value": Decimal("100.00"),
        "description": "Expense prediction.",
    }

    def test_auth_required(
        self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401.
        """
        prediction = expense_prediction_factory()
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.patch(url, {})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        expense_prediction = expense_prediction_factory(budget=budget)
        url = expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called with PATCH by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        prediction = expense_prediction_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.patch(url, {})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize(
        "param, value",
        [
            ("current_value", Decimal("200.00")),
            ("description", "New description"),
        ],
    )
    @pytest.mark.django_db
    def test_prediction_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called with PATCH by User belonging to Budget.
        THEN: HTTP 200, ExpensePrediction updated.
        """
        budget = budget_factory(members=[base_user])
        prediction = expense_prediction_factory(budget=budget, **self.PAYLOAD)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(budget.id, prediction.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        prediction.refresh_from_db()
        assert getattr(prediction, param) == update_payload[param]

    def test_prediction_update_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database. Update payload with "category" value prepared.
        WHEN: ExpensePredictionViewSet detail view called with PATCH by User belonging to Budget with valid payload.
        THEN: HTTP 200, Deposit updated with "category" value.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        prediction = expense_prediction_factory(budget=budget, **self.PAYLOAD)
        update_payload = {"category": category.id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(budget.id, prediction.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        prediction.refresh_from_db()
        assert prediction.category == category

    def test_error_update_category_does_not_belong_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. TransferCategory not belonging to Budget as
        'category' in payload.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        budget = budget_factory(members=[base_user])
        prediction = expense_prediction_factory(budget=budget)
        payload = {"category": transfer_category_factory(category_type=CategoryType.EXPENSE).id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0] == "Budget for period and category fields is not the same."
        )

    def test_error_category_not_with_expense_type(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. INCOME TransferCategory as 'category' in payload.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        budget = budget_factory(members=[base_user])
        prediction = expense_prediction_factory(budget=budget)
        payload = {"category": transfer_category_factory(budget=budget, category_type=CategoryType.INCOME).id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "Incorrect category provided. Please provide expense category."

    def test_error_change_prediction_for_closed_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance created in database.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with valid payload, but when
        the BudgetingPeriod of prediction is CLOSED.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, status=PeriodStatus.DRAFT)
        prediction = expense_prediction_factory(period=period)
        period.status = PeriodStatus.CLOSED
        period.save()
        payload = {"current_value": Decimal("123.45")}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Expense Prediction cannot be changed when Budgeting Period is closed."
        )

    def test_update_prediction_for_active_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance created in database.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with valid payload, but when
        the BudgetingPeriod of prediction is ACTIVE.
        THEN: HTTP 200 returned. ExpensePrediction updated.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, status=PeriodStatus.DRAFT)
        prediction = expense_prediction_factory(period=period, current_value=Decimal("100.00"))
        period.status = PeriodStatus.ACTIVE
        period.save()
        payload = {"current_value": Decimal("123.45")}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        prediction.refresh_from_db()
        assert prediction.current_value == Decimal("123.45")

    def test_error_change_period_of_prediction(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance created in database.
        WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with other BudgetingPeriod
        in payload.
        THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        prediction = expense_prediction_factory(period=period)
        payload = {"period": budgeting_period_factory(budget=budget).id}
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data["detail"]
        assert response.data["detail"]["period"][0] == "Budgeting Period for Expense Prediction cannot be changed."


@pytest.mark.django_db
class TestExpensePredictionViewSetDelete:
    """Tests for delete ExpensePrediction on ExpensePredictionViewSet."""

    def test_auth_required(
        self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called with DELETE without authentication.
        THEN: Unauthorized HTTP 401.
        """
        prediction = expense_prediction_factory()
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: ExpensePredictionViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        budget = budget_factory(members=[base_user])
        expense_prediction = expense_prediction_factory(budget=budget)
        url = expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called with DELETE by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        prediction = expense_prediction_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(prediction.period.budget.id, prediction.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_delete_prediction(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction instance for Budget created in database.
        WHEN: ExpensePredictionViewSet detail view called with DELETE by User belonging to Budget.
        THEN: No content HTTP 204, ExpensePrediction deleted.
        """
        budget = budget_factory(members=[base_user])
        prediction = expense_prediction_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = expense_prediction_detail_url(budget.id, prediction.id)

        assert ExpensePrediction.objects.filter(period__budget=budget).count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ExpensePrediction.objects.filter(period__budget=budget).exists()
