import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from predictions.models import ExpensePrediction
from predictions.serializers import ExpensePredictionSerializer
from rest_framework import status
from rest_framework.test import APIClient


def expense_prediction_url(budget_id: int):
    """Create and return an ExpensePrediction list URL."""
    return reverse('budgets:expense_prediction-list', args=[budget_id])


def expense_prediction_detail_url(budget_id: int, prediction_id: int):
    """Create and return an ExpensePrediction detail URL."""
    return reverse('budgets:expense_prediction-detail', args=[budget_id, prediction_id])


@pytest.mark.django_db
class TestExpensePredictionApiAccess:
    """Tests for access to ExpensePredictionViewSet."""

    def test_auth_required_on_list_view(self, api_client: APIClient, expense_prediction: ExpensePrediction):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(expense_prediction_url(expense_prediction.period.budget.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_required_on_detail_view(self, api_client: APIClient, expense_prediction: ExpensePrediction):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet detail method called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(
            expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member_on_list_view(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        expense_prediction = expense_prediction_factory()

        api_client.force_authenticate(other_user)

        response = api_client.get(expense_prediction_url(expense_prediction.period.budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'

    def test_user_not_budget_member_on_detail_view(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet detail method called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        expense_prediction = expense_prediction_factory()
        api_client.force_authenticate(other_user)

        response = api_client.get(
            expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


@pytest.mark.django_db
class TestExpensePredictionApiList:
    """Tests for list view on ExpensePredictionViewSet."""

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
        budget = budget_factory(owner=base_user)
        for _ in range(2):
            expense_prediction_factory(budget=budget)

        response = api_client.get(expense_prediction_url(budget.id))

        predictions = ExpensePrediction.objects.filter(period__budget=budget)
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

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
        budget = budget_factory(owner=base_user)
        prediction = expense_prediction_factory(budget=budget)
        expense_prediction_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id))

        predictions = ExpensePrediction.objects.filter(period__budget=budget)
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(serializer.data) == predictions.count() == 1
        assert response.data['results'] == serializer.data
        assert response.data['results'][0]['id'] == prediction.id

    @pytest.mark.parametrize('sort_param', ('id', '-id', 'period', '-period', 'category', '-category'))
    def test_get_predictions_list_sorted_by_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Three ExpensePrediction objects created in database.
        WHEN: The ExpensePredictionViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all ExpensePrediction existing in database sorted by given param.
        """
        budget = budget_factory(owner=base_user)
        for _ in range(5):
            expense_prediction_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={'ordering': sort_param})

        assert response.status_code == status.HTTP_200_OK
        predictions = ExpensePrediction.objects.all().order_by(sort_param)
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.data['results'] and serializer.data
        assert len(response.data['results']) == len(serializer.data) == len(predictions) == 3
        assert response.data['results'] == serializer.data

    # @pytest.mark.parametrize(
    #     'filter_value', ('Test', 'TEST', 'test', 'name', 'NAME', 'Name', 'Test name', 'TEST NAME', 'test name')
    # )
    # def test_get_predictions_list_filtered_by_name(
    #     self,
    #     api_client: APIClient,
    #     base_user: AbstractUser,
    #     budget_factory: FactoryMetaClass,
    #     expense_prediction_factory: FactoryMetaClass,
    #     filter_value: str,
    # ):
    #     """
    #     GIVEN: Two ExpensePrediction objects for single Budget.
    #     WHEN: The ExpensePredictionViewSet list view is called with name filter.
    #     THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
    #     name value.
    #     """
    #     budget = budget_factory(owner=base_user)
    #     prediction = expense_prediction_factory(name='Test name', budget=budget)
    #     expense_prediction_factory(name='Other prediction', budget=budget)
    #     api_client.force_authenticate(base_user)
    #
    #     response = api_client.get(expense_prediction_url(budget.id), data={'name': filter_value})
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert ExpensePrediction.objects.all().count() == 2
    #     predictions = ExpensePrediction.objects.filter(budget=prediction.budget, name__icontains=filter_value)
    #     serializer = ExpensePredictionSerializer(
    #         predictions,
    #         many=True,
    #     )
    #     assert response.data['results'] and serializer.data
    #     assert len(response.data['results']) == len(serializer.data) == predictions.count() == 1
    #     assert response.data['results'] == serializer.data
    #     assert response.data['results'][0]['id'] == prediction.id
    #
    # def test_get_predictions_list_filtered_by_common_only_true(
    #     self,
    #     api_client: APIClient,
    #     base_user: AbstractUser,
    #     budget_factory: FactoryMetaClass,
    #     expense_prediction_factory: FactoryMetaClass,
    # ):
    #     """
    #     GIVEN: Two ExpensePrediction objects for single Budget.
    #     WHEN: The ExpensePredictionViewSet list view is called with True common_only filter.
    #     THEN: Response must contain only common ExpensePrediction objects existing in database assigned to Budget.
    #     """
    #     budget = budget_factory(owner=base_user)
    #     prediction = expense_prediction_factory(budget=budget, owner=None)
    #     expense_prediction_factory(budget=budget, owner=base_user)
    #     api_client.force_authenticate(base_user)
    #
    #     response = api_client.get(expense_prediction_url(budget.id), data={'common_only': True})
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert ExpensePrediction.objects.all().count() == 2
    #     predictions = ExpensePrediction.objects.filter(budget=prediction.budget, owner__isnull=True)
    #     serializer = ExpensePredictionSerializer(predictions, many=True)
    #     assert response.data['results'] and serializer.data
    #     assert len(response.data['results']) == len(serializer.data) == predictions.count() == 1
    #     assert response.data['results'] == serializer.data
    #     assert response.data['results'][0]['id'] == prediction.id
    #
    # def test_get_predictions_list_filtered_by_common_only_false(
    #     self,
    #     api_client: APIClient,
    #     base_user: AbstractUser,
    #     budget_factory: FactoryMetaClass,
    #     expense_prediction_factory: FactoryMetaClass,
    # ):
    #     """
    #     GIVEN: Two ExpensePrediction objects for single Budget.
    #     WHEN: The ExpensePredictionViewSet list view is called with False common_only filter.
    #     THEN: Response must contain all ExpensePrediction objects existing in database assigned to Budget.
    #     """
    #     budget = budget_factory(owner=base_user)
    #     expense_prediction_factory(budget=budget, owner=base_user)
    #     expense_prediction_factory(budget=budget, owner=None)
    #     api_client.force_authenticate(base_user)
    #
    #     response = api_client.get(expense_prediction_url(budget.id), data={'common_only': False})
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert ExpensePrediction.objects.all().count() == 2
    #     predictions = ExpensePrediction.objects.filter(budget=budget)
    #     serializer = ExpensePredictionSerializer(predictions, many=True)
    #     assert response.data['results'] and serializer.data
    #     assert len(response.data['results']) == len(serializer.data) == predictions.count() == 2
    #     assert response.data['results'] == serializer.data
    #
    # def test_get_predictions_list_filtered_by_group(
    #     self,
    #     api_client: APIClient,
    #     base_user: AbstractUser,
    #     budget_factory: FactoryMetaClass,
    #     expense_prediction_factory: FactoryMetaClass,
    # ):
    #     """
    #     GIVEN: Two ExpensePrediction objects for single Budget.
    #     WHEN: The ExpensePredictionViewSet list view is called with group filter.
    #     THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
    #     group value.
    #     """
    #     budget = budget_factory(owner=base_user)
    #     prediction = expense_prediction_factory(group=ExpensePrediction.IncomeGroups.REGULAR, budget=budget)
    #     expense_prediction_factory(group=ExpensePrediction.IncomeGroups.IRREGULAR, budget=budget)
    #     api_client.force_authenticate(base_user)
    #
    #     response = api_client.get(
    #         expense_prediction_url(budget.id), data={'group': ExpensePrediction.IncomeGroups.REGULAR.value}
    #     )
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert ExpensePrediction.objects.all().count() == 2
    #     predictions = ExpensePrediction.objects.filter(
    #         budget=prediction.budget, group=ExpensePrediction.IncomeGroups.REGULAR.value
    #     )
    #     serializer = ExpensePredictionSerializer(predictions, many=True)
    #     assert response.data['results'] and serializer.data
    #     assert len(response.data['results']) == len(serializer.data) == predictions.count() == 1
    #     assert response.data['results'] == serializer.data
    #     assert response.data['results'][0]['id'] == prediction.id
    #
    # def test_get_predictions_list_filtered_by_owner(
    #     self,
    #     api_client: APIClient,
    #     base_user: AbstractUser,
    #     budget_factory: FactoryMetaClass,
    #     expense_prediction_factory: FactoryMetaClass,
    # ):
    #     """
    #     GIVEN: Two ExpensePrediction objects for single Budget.
    #     WHEN: The ExpensePredictionViewSet list view is called with owner filter.
    #     THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
    #     owner value.
    #     """
    #     budget = budget_factory(owner=base_user)
    #     prediction = expense_prediction_factory(budget=budget, owner=base_user)
    #     expense_prediction_factory(budget=budget, owner=None)
    #     api_client.force_authenticate(base_user)
    #
    #     response = api_client.get(expense_prediction_url(budget.id), data={'owner': base_user.id})
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert ExpensePrediction.objects.all().count() == 2
    #     predictions = ExpensePrediction.objects.filter(budget=prediction.budget, owner=base_user)
    #     serializer = ExpensePredictionSerializer(predictions, many=True)
    #     assert response.data['results'] and serializer.data
    #     assert len(response.data['results']) == len(serializer.data) == predictions.count() == 1
    #     assert response.data['results'] == serializer.data
    #     assert response.data['results'][0]['id'] == prediction.id
    #
    # @pytest.mark.parametrize('is_active', (True, False))
    # def test_get_predictions_list_filtered_by_is_active(
    #     self,
    #     api_client: APIClient,
    #     base_user: AbstractUser,
    #     budget_factory: FactoryMetaClass,
    #     expense_prediction_factory: FactoryMetaClass,
    #     is_active: bool,
    # ):
    #     """
    #     GIVEN: Two ExpensePrediction objects for single Budget.
    #     WHEN: The ExpensePredictionViewSet list view is called with is_active filter.
    #     THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
    #     is_active value.
    #     """
    #     budget = budget_factory(owner=base_user)
    #     prediction = expense_prediction_factory(budget=budget, is_active=is_active)
    #     expense_prediction_factory(budget=budget, is_active=not is_active)
    #     api_client.force_authenticate(base_user)
    #
    #     response = api_client.get(expense_prediction_url(budget.id), data={'is_active': is_active})
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert ExpensePrediction.objects.all().count() == 2
    #     predictions = ExpensePrediction.objects.filter(budget=prediction.budget, is_active=is_active)
    #     serializer = ExpensePredictionSerializer(predictions, many=True)
    #     assert response.data['results'] and serializer.data
    #     assert len(response.data['results']) == len(serializer.data) == predictions.count() == 1
    #     assert response.data['results'] == serializer.data
    #     assert response.data['results'][0]['id'] == prediction.id
