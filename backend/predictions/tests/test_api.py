import pytest
from budgets.models import Budget
from django.urls import reverse
from factory.base import FactoryMetaClass
from predictions.models import ExpensePrediction
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
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet list method called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        period = budgeting_period_factory(budget=budget)
        category = expense_category_factory(budget=budget)
        expense_prediction = expense_prediction_factory(period=period, category=category)
        api_client.force_authenticate(other_user)

        response = api_client.get(expense_prediction_url(expense_prediction.period.budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'

    def test_user_not_budget_member_on_detail_view(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePrediction model instance in database.
        WHEN: ExpensePredictionViewSet detail method called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        period = budgeting_period_factory(budget=budget)
        category = expense_category_factory(budget=budget)
        expense_prediction = expense_prediction_factory(period=period, category=category)
        api_client.force_authenticate(other_user)

        response = api_client.get(
            expense_prediction_detail_url(expense_prediction.period.budget.id, expense_prediction.id)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


# @pytest.mark.django_db
# class TestExpensePredictionApiList:
#     """Tests for list view on ExpensePredictionViewSet."""
#
#     def test_retrieve_prediction_list_by_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two ExpensePrediction model instances for single Budget created in database.
#         WHEN: ExpensePredictionViewSet called by Budget owner.
#         THEN: Response with serialized Budget ExpensePrediction list returned.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         for _ in range(2):
#             expense_prediction_factory(budget=budget)
#
#         response = api_client.get(expense_prediction_url(budget.id))
#
#         categories = ExpensePrediction.objects.filter(budget=budget)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data['results'] == serializer.data
#
#     def test_retrieve_prediction_list_by_member(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two ExpensePrediction model instances for single Budget created in database.
#         WHEN: ExpensePredictionViewSet called by Budget member.
#         THEN: Response with serialized Budget ExpensePrediction list returned.
#         """
#         budget = budget_factory(members=[base_user])
#         api_client.force_authenticate(base_user)
#         for _ in range(2):
#             expense_prediction_factory(budget=budget)
#
#         response = api_client.get(expense_prediction_url(budget.id))
#
#         categories = ExpensePrediction.objects.filter(budget=budget)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data['results'] == serializer.data
#
#     def test_prediction_list_limited_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two ExpensePrediction model instances for different Budgets created in database.
#         WHEN: ExpensePredictionViewSet called by one of Budgets owner.
#         THEN: Response with serialized ExpensePrediction list (only from given Budget) returned.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget)
#         expense_prediction_factory()
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(expense_prediction_url(budget.id))
#
#         categories = ExpensePrediction.objects.filter(budget=budget)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == prediction.id
#
#     @pytest.mark.parametrize('sort_param', ('id', '-id', 'group', '-group', 'name', '-name'))
#     def test_get_categories_list_sorted_by_param(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#         sort_param: str,
#     ):
#         """
#         GIVEN: Three ExpensePrediction objects created in database.
#         WHEN: The ExpensePredictionViewSet list view is called with sorting by given param and without any filters.
#         THEN: Response must contain all ExpensePrediction existing in database sorted by given param.
#         """
#         budget = budget_factory(owner=base_user)
#         for _ in range(3):
#             expense_prediction_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(expense_prediction_url(budget.id), data={'ordering': sort_param})
#
#         assert response.status_code == status.HTTP_200_OK
#         categories = ExpensePrediction.objects.all().order_by(sort_param)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.data['results'] and serializer.data
#         assert len(response.data['results']) == len(serializer.data) == len(categories) == 3
#         assert response.data['results'] == serializer.data
#
#     @pytest.mark.parametrize(
#         'filter_value', ('Test', 'TEST', 'test', 'name', 'NAME', 'Name', 'Test name', 'TEST NAME', 'test name')
#     )
#     def test_get_categories_list_filtered_by_name(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#         filter_value: str,
#     ):
#         """
#         GIVEN: Two ExpensePrediction objects for single Budget.
#         WHEN: The ExpensePredictionViewSet list view is called with name filter.
#         THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
#         name value.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(name='Test name', budget=budget)
#         expense_prediction_factory(name='Other prediction', budget=budget)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(expense_prediction_url(budget.id), data={'name': filter_value})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert ExpensePrediction.objects.all().count() == 2
#         categories = ExpensePrediction.objects.filter(budget=prediction.budget, name__icontains=filter_value)
#         serializer = ExpensePredictionSerializer(
#             categories,
#             many=True,
#         )
#         assert response.data['results'] and serializer.data
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == prediction.id
#
#     def test_get_categories_list_filtered_by_common_only_true(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two ExpensePrediction objects for single Budget.
#         WHEN: The ExpensePredictionViewSet list view is called with True common_only filter.
#         THEN: Response must contain only common ExpensePrediction objects existing in database assigned to Budget.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget, owner=None)
#         expense_prediction_factory(budget=budget, owner=base_user)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(expense_prediction_url(budget.id), data={'common_only': True})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert ExpensePrediction.objects.all().count() == 2
#         categories = ExpensePrediction.objects.filter(budget=prediction.budget, owner__isnull=True)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.data['results'] and serializer.data
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == prediction.id
#
#     def test_get_categories_list_filtered_by_common_only_false(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two ExpensePrediction objects for single Budget.
#         WHEN: The ExpensePredictionViewSet list view is called with False common_only filter.
#         THEN: Response must contain all ExpensePrediction objects existing in database assigned to Budget.
#         """
#         budget = budget_factory(owner=base_user)
#         expense_prediction_factory(budget=budget, owner=base_user)
#         expense_prediction_factory(budget=budget, owner=None)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(expense_prediction_url(budget.id), data={'common_only': False})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert ExpensePrediction.objects.all().count() == 2
#         categories = ExpensePrediction.objects.filter(budget=budget)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.data['results'] and serializer.data
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 2
#         assert response.data['results'] == serializer.data
#
#     def test_get_categories_list_filtered_by_group(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two ExpensePrediction objects for single Budget.
#         WHEN: The ExpensePredictionViewSet list view is called with group filter.
#         THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
#         group value.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(group=ExpensePrediction.IncomeGroups.REGULAR, budget=budget)
#         expense_prediction_factory(group=ExpensePrediction.IncomeGroups.IRREGULAR, budget=budget)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(
#             expense_prediction_url(budget.id), data={'group': ExpensePrediction.IncomeGroups.REGULAR.value}
#         )
#
#         assert response.status_code == status.HTTP_200_OK
#         assert ExpensePrediction.objects.all().count() == 2
#         categories = ExpensePrediction.objects.filter(
#             budget=prediction.budget, group=ExpensePrediction.IncomeGroups.REGULAR.value
#         )
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.data['results'] and serializer.data
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == prediction.id
#
#     def test_get_categories_list_filtered_by_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two ExpensePrediction objects for single Budget.
#         WHEN: The ExpensePredictionViewSet list view is called with owner filter.
#         THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
#         owner value.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget, owner=base_user)
#         expense_prediction_factory(budget=budget, owner=None)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(expense_prediction_url(budget.id), data={'owner': base_user.id})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert ExpensePrediction.objects.all().count() == 2
#         categories = ExpensePrediction.objects.filter(budget=prediction.budget, owner=base_user)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.data['results'] and serializer.data
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == prediction.id
#
#     @pytest.mark.parametrize('is_active', (True, False))
#     def test_get_categories_list_filtered_by_is_active(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#         is_active: bool,
#     ):
#         """
#         GIVEN: Two ExpensePrediction objects for single Budget.
#         WHEN: The ExpensePredictionViewSet list view is called with is_active filter.
#         THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
#         is_active value.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget, is_active=is_active)
#         expense_prediction_factory(budget=budget, is_active=not is_active)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(expense_prediction_url(budget.id), data={'is_active': is_active})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert ExpensePrediction.objects.all().count() == 2
#         categories = ExpensePrediction.objects.filter(budget=prediction.budget, is_active=is_active)
#         serializer = ExpensePredictionSerializer(categories, many=True)
#         assert response.data['results'] and serializer.data
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == prediction.id
#
#
# @pytest.mark.django_db
# class TestExpensePredictionApiCreate:
#     """Tests for create ExpensePrediction on ExpensePredictionViewSet."""
#
#     PAYLOAD = {
#         'name': 'Salary',
#         'group': ExpensePrediction.IncomeGroups.REGULAR,
#         'description': 'Monthly salary.',
#         'is_active': True,
#     }
#
#     @pytest.mark.parametrize('user_type', ['owner', 'member'])
#     def test_create_single_prediction(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         user_type: str,
#     ):
#         """
#         GIVEN: Budget instances created in database. Valid payload prepared
#         for ExpensePrediction.
#         WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with valid payload.
#         THEN: ExpensePrediction object created in database with given payload
#         """
#         other_user = user_factory()
#         if user_type == 'owner':
#             budget = budget_factory(owner=base_user, members=[other_user])
#         else:
#             budget = budget_factory(members=[base_user, other_user])
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(expense_prediction_url(budget.id), self.PAYLOAD)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         assert ExpensePrediction.objects.filter(budget=budget).count() == 1
#         prediction = ExpensePrediction.objects.get(id=response.data['id'])
#         for key in self.PAYLOAD:
#             assert getattr(prediction, key) == self.PAYLOAD[key]
#         serializer = ExpensePredictionSerializer(prediction)
#         assert response.data == serializer.data
#
#     def test_create_prediction_with_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instances created in database. Valid payload with owner prepared
#         for ExpensePrediction.
#         WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with valid payload.
#         THEN: ExpensePrediction object created in database with given payload
#         """
#         budget = budget_factory(owner=base_user)
#         payload = self.PAYLOAD.copy()
#         payload['owner'] = base_user.id
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(expense_prediction_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         prediction = ExpensePrediction.objects.get(id=response.data['id'])
#         assert prediction.owner == base_user
#         assert base_user.personal_income_categories.filter(budget=budget).count() == 1
#         serializer = ExpensePredictionSerializer(prediction)
#         assert response.data == serializer.data
#
#     def test_create_two_categories_for_single_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instances created in database. Valid payloads prepared
#         for two ExpenseCategories.
#         WHEN: ExpensePredictionViewSet called twice with POST by User belonging to Budget with valid payloads.
#         THEN: Two ExpensePrediction objects created in database with given payloads.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         payload_1 = self.PAYLOAD.copy()
#         payload_1['name'] = 'ExpensePrediction name 1'
#         payload_2 = self.PAYLOAD.copy()
#         payload_2['name'] = 'ExpensePrediction name 2'
#
#         response_1 = api_client.post(expense_prediction_url(budget.id), payload_1)
#         response_2 = api_client.post(expense_prediction_url(budget.id), payload_2)
#
#         assert response_1.status_code == status.HTTP_201_CREATED
#         assert response_2.status_code == status.HTTP_201_CREATED
#         assert ExpensePrediction.objects.filter(budget=budget).count() == 2
#         for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
#             prediction = ExpensePrediction.objects.get(id=response.data['id'])
#             for key in payload:
#                 assert getattr(prediction, key) == payload[key]
#
#     def test_create_same_prediction_for_two_budgets(self, api_client: APIClient, budget_factory: FactoryMetaClass):
#         """
#         GIVEN: Two Budget instances created in database. Valid payload prepared for two ExpenseCategories.
#         WHEN: ExpensePredictionViewSet called twice with POST by different Users belonging to two different
#         Budgets with valid payload.
#         THEN: Two ExpensePrediction objects created in database with given payload for separate Budgets.
#         """
#         payload = self.PAYLOAD.copy()
#         budget_1 = budget_factory()
#         budget_2 = budget_factory()
#
#         api_client.force_authenticate(budget_1.owner)
#         api_client.post(expense_prediction_url(budget_1.id), payload)
#         api_client.force_authenticate(budget_2.owner)
#         api_client.post(expense_prediction_url(budget_2.id), payload)
#
#         assert ExpensePrediction.objects.all().count() == 2
#         assert ExpensePrediction.objects.filter(budget=budget_1).count() == 1
#         assert ExpensePrediction.objects.filter(budget=budget_2).count() == 1
#
#     @pytest.mark.parametrize('field_name', ['name', 'description'])
#     def test_error_value_too_long(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         field_name: str,
#     ):
#         """
#         GIVEN: Budget instance created in database. Payload for ExpensePrediction with field value too long.
#         WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. ExpensePrediction not created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         max_length = ExpensePrediction._meta.get_field(field_name).max_length
#         payload = self.PAYLOAD.copy()
#         payload[field_name] = (max_length + 1) * 'a'
#
#         response = api_client.post(expense_prediction_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert field_name in response.data
#         assert response.data[field_name][0] == f'Ensure this field has no more than {max_length} characters.'
#         assert not ExpensePrediction.objects.filter(budget=budget).exists()
#
#     def test_error_create_prediction_for_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload for ExpensePrediction.
#         WHEN: ExpensePredictionViewSet called with POST by User not belonging to Budget with valid payload.
#         THEN: Forbidden HTTP 403 returned. Object not created.
#         """
#         budget = budget_factory()
#         payload = self.PAYLOAD.copy()
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(expense_prediction_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#         assert not ExpensePrediction.objects.filter(budget=budget).exists()
#
#     def test_error_owner_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instance created in database. User not belonging to Budget as
#         'owner' in payload.
#         WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. No ExpensePrediction created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         outer_user = user_factory()
#         payload = self.PAYLOAD.copy()
#
#         payload['owner'] = outer_user.id
#         api_client.force_authenticate(base_user)
#
#         api_client.post(expense_prediction_url(budget.id), payload)
#         response = api_client.post(expense_prediction_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Provided owner does not belong to Budget.'
#         assert not ExpensePrediction.objects.filter(budget=budget).exists()
#
#     def test_error_personal_prediction_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance with owner created in database. Name of existing personal ExpensePrediction
#         and owner of existing ExpensePrediction in payload.
#         WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. No ExpensePrediction created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         payload = self.PAYLOAD.copy()
#         payload['owner'] = base_user.id
#         api_client.force_authenticate(base_user)
#         api_client.post(expense_prediction_url(budget.id), payload)
#
#         response = api_client.post(expense_prediction_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0]
#             == 'Personal ExpensePrediction with given name already exists in Budget for provided owner.'
#         )
#         assert ExpensePrediction.objects.filter(budget=budget, owner__isnull=False).count() == 1
#
#     def test_error_common_prediction_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance with owner created in database. Name of existing common
#         ExpensePrediction in payload.
#         WHEN: ExpensePredictionViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. No ExpensePrediction created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         payload = self.PAYLOAD.copy()
#         api_client.force_authenticate(base_user)
#         api_client.post(expense_prediction_url(budget.id), payload)
#
#         response = api_client.post(expense_prediction_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Common ExpensePrediction with given name
#         already exists in Budget.'
#         assert ExpensePrediction.objects.filter(budget=budget, owner__isnull=True).count() == 1
#
#
# @pytest.mark.django_db
# class TestExpensePredictionApiDetail:
#     """Tests for detail view on ExpensePredictionViewSet."""
#
#     @pytest.mark.parametrize('user_type', ['owner', 'member'])
#     def test_get_prediction_details(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#         user_type: str,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called by User belonging to Budget.
#         THEN: HTTP 200, ExpensePrediction details returned.
#         """
#         if user_type == 'owner':
#             budget = budget_factory(owner=base_user)
#         else:
#             budget = budget_factory(members=[base_user])
#         prediction = expense_prediction_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(budget.id, prediction.id)
#
#         response = api_client.get(url)
#         serializer = ExpensePredictionSerializer(prediction)
#
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data == serializer.data
#
#     def test_error_get_prediction_details_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         prediction = expense_prediction_factory()
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_get_details_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         prediction = expense_prediction_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#
# @pytest.mark.django_db
# class TestExpensePredictionApiPartialUpdate:
#     """Tests for partial update view on ExpensePredictionViewSet."""
#
#     PAYLOAD = {
#         'name': 'Salary',
#         'group': ExpensePrediction.IncomeGroups.REGULAR,
#         'description': 'Monthly salary.',
#         'is_active': True,
#     }
#
#     @pytest.mark.parametrize(
#         'param, value',
#         [
#             ('name', 'New name'),
#             ('group', ExpensePrediction.IncomeGroups.IRREGULAR),
#             ('description', 'New description'),
#             ('is_active', False),
#         ],
#     )
#     @pytest.mark.django_db
#     def test_prediction_partial_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with PATCH by User belonging to Budget.
#         THEN: HTTP 200, ExpensePrediction updated.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget, owner=None, **self.PAYLOAD)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(budget.id, prediction.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         prediction.refresh_from_db()
#         assert getattr(prediction, param) == update_payload[param]
#         assert prediction.owner is None
#
#     def test_prediction_partial_update_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database. Update payload with "owner" value prepared.
#         WHEN: ExpensePredictionSet detail view called with PATCH by User belonging to Budget with valid payload.
#         THEN: HTTP 200, Deposit updated with "owner" value.
#         """
#         member = user_factory()
#         budget = budget_factory(owner=base_user, members=[member])
#         prediction = expense_prediction_factory(budget=budget, owner=None, **self.PAYLOAD)
#         update_payload = {'owner': member.id}
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(budget.id, prediction.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         prediction.refresh_from_db()
#         assert prediction.owner == member
#
#     def test_error_partial_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with PATCH without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         prediction = expense_prediction_factory()
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_partial_update_prediction_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with PATCH by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         prediction = expense_prediction_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     def test_error_partial_update_owner_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instance created in database. User not belonging to Budget as
#         'owner' in payload.
#         WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget)
#         payload = {'owner': user_factory().id}
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Provided owner does not belong to Budget.'
#
#     def test_error_partial_update_personal_prediction_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance with owner created in database. Name of existing personal ExpensePrediction
#         in payload.
#         WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         expense_prediction_factory(budget=budget, owner=base_user, **self.PAYLOAD)
#         prediction = expense_prediction_factory(budget=budget, owner=base_user)
#         payload = {'name': self.PAYLOAD['name']}
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0]
#             == 'Personal ExpensePrediction with given name already exists in Budget for provided owner.'
#         )
#
#     def test_error_partial_update_common_prediction_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance with owner created in database. Name of existing personal ExpensePrediction
#         and owner of existing ExpensePrediction in payload.
#         WHEN: ExpensePredictionViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         expense_prediction_factory(budget=budget, owner=None, **self.PAYLOAD)
#         prediction = expense_prediction_factory(budget=budget, owner=None)
#         payload = {'name': self.PAYLOAD['name']}
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Common ExpensePrediction with given name
#         already exists in Budget.'
#
#
# @pytest.mark.django_db
# class TestExpensePredictionApiFullUpdate:
#     """Tests for full update view on ExpensePredictionViewSet."""
#
#     INITIAL_PAYLOAD = {
#         'name': 'Salary',
#         'group': ExpensePrediction.IncomeGroups.REGULAR,
#         'description': 'Monthly salary.',
#         'is_active': True,
#     }
#
#     UPDATE_PAYLOAD = {
#         'name': 'Additional',
#         'group': ExpensePrediction.IncomeGroups.IRREGULAR,
#         'description': 'Extra cash.',
#         'is_active': False,
#     }
#
#     @pytest.mark.django_db
#     def test_prediction_full_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with PUT by User belonging to Budget.
#         THEN: HTTP 200, ExpensePrediction updated.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget, owner=None, **self.INITIAL_PAYLOAD)
#         update_payload = self.UPDATE_PAYLOAD.copy()
#         update_payload['owner'] = base_user.id
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(budget.id, prediction.id)
#
#         response = api_client.put(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         prediction.refresh_from_db()
#         for param in update_payload:
#             if param == 'owner':
#                 assert getattr(prediction, param) == base_user
#                 continue
#             assert getattr(prediction, param) == update_payload[param]
#
#     def test_error_full_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         prediction = expense_prediction_factory()
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_full_update_prediction_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with PUT by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         prediction = expense_prediction_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     def test_error_full_update_owner_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instance created in database. User not belonging to Budget as
#         'owner' in payload.
#         WHEN: ExpensePredictionViewSet called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget)
#         payload = self.UPDATE_PAYLOAD.copy()
#         payload['owner'] = user_factory().id
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.put(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Provided owner does not belong to Budget.'
#
#     def test_error_full_update_personal_prediction_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance with owner created in database. Name of existing personal ExpensePrediction
#         in payload.
#         WHEN: ExpensePredictionViewSet called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         expense_prediction_factory(budget=budget, owner=base_user, **self.INITIAL_PAYLOAD)
#         prediction = expense_prediction_factory(budget=budget, owner=base_user)
#         payload = self.UPDATE_PAYLOAD.copy()
#         payload['name'] = self.INITIAL_PAYLOAD['name']
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.put(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0]
#             == 'Personal ExpensePrediction with given name already exists in Budget for provided owner.'
#         )
#
#     def test_error_full_update_common_prediction_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance with owner created in database. Name of existing personal ExpensePrediction
#         and owner of existing ExpensePrediction in payload.
#         WHEN: ExpensePredictionViewSet called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. ExpensePrediction not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         expense_prediction_factory(budget=budget, owner=None, **self.INITIAL_PAYLOAD)
#         prediction = expense_prediction_factory(budget=budget, owner=None)
#         payload = self.UPDATE_PAYLOAD.copy()
#         payload['name'] = self.INITIAL_PAYLOAD['name']
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.put(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Common ExpensePrediction with given name already
#         exists in Budget.'
#
#
# @pytest.mark.django_db
# class TestExpensePredictionApiDelete:
#     """Tests for delete ExpensePrediction on ExpensePredictionViewSet."""
#
#     def test_delete_prediction(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with DELETE by User belonging to Budget.
#         THEN: No content HTTP 204, ExpensePrediction deleted.
#         """
#         budget = budget_factory(owner=base_user)
#         prediction = expense_prediction_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(budget.id, prediction.id)
#
#         assert ExpensePrediction.objects.filter(budget=budget).count() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not ExpensePrediction.objects.filter(budget=budget).exists()
#
#     def test_error_delete_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, expense_prediction_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with DELETE without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         prediction = expense_prediction_factory()
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_delete_prediction_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_prediction_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: ExpensePrediction instance for Budget created in database.
#         WHEN: ExpensePredictionViewSet detail view called with DELETE by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         prediction = expense_prediction_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = expense_prediction_detail_url(prediction.budget.id, prediction.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
