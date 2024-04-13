import pytest
from budgets.models import Budget
from deposits.models import Deposit
from deposits.serializers import DepositSerializer
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient


def deposit_url(budget_id):
    """Create and return a deposit detail URL."""
    return reverse('budgets:deposit-list', args=[budget_id])


def deposit_detail_url(budget_id, deposit_id):
    """Create and return a deposit detail URL."""
    return reverse('budgets:deposit-detail', args=[budget_id, deposit_id])


@pytest.mark.django_db
class TestDepositApiAccess:
    """Tests for access to DepositViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: DepositViewSet called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(deposit_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: DepositViewSet called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(deposit_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


@pytest.mark.django_db
class TestDepositApiList:
    """Tests for list view on DepositViewSet."""

    def test_retrieve_deposits_list_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit model instances for single Budget created in database.
        WHEN: DepositViewSet called by Budget owner.
        THEN: Response with serialized Budget Deposit list returned.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        for _ in range(2):
            deposit_factory(budget=budget)

        response = api_client.get(deposit_url(budget.id))

        deposits = Deposit.objects.filter(budget=budget)
        serializer = DepositSerializer(deposits, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_retrieve_deposits_list_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit model instances for single Budget created in database.
        WHEN: DepositViewSet called by Budget member.
        THEN: Response with serialized Budget Deposit list returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        for _ in range(2):
            deposit_factory(budget=budget)

        response = api_client.get(deposit_url(budget.id))

        deposits = Deposit.objects.filter(budget=budget)
        serializer = DepositSerializer(deposits, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_deposits_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit model instances for different Budgets created in database.
        WHEN: DepositViewSet called by one of Budgets owner.
        THEN: Response with serialized Deposit list (only from given Budget) returned.
        """
        budget = budget_factory(owner=base_user)
        deposit = deposit_factory(budget=budget)
        deposit_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(deposit_url(budget.id))

        deposits = Deposit.objects.filter(budget=budget)
        serializer = DepositSerializer(deposits, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(serializer.data) == deposits.count() == 1
        assert response.data['results'] == serializer.data
        assert response.data['results'][0]['id'] == deposit.id


@pytest.mark.django_db
class TestDepositApiCreate:
    """Tests for create Deposit on DepositViewSet."""

    PAYLOAD = {
        'name': 'Deposit name',
        'description': 'Deposit description',
        'deposit_type': Deposit.DepositTypes.PERSONAL,
        'is_active': True,
    }

    @pytest.mark.parametrize('user_type', ['owner', 'member'])
    @pytest.mark.parametrize('with_owner', [True, False])
    def test_create_single_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        user_type: str,
        with_owner: bool,
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for Deposit.
        WHEN: DepositViewSet called with POST by User belonging to Budget with valid payload.
        THEN: Deposit object created in database with given payload
        """
        other_user = user_factory()
        if user_type == 'owner':
            budget = budget_factory(owner=base_user, members=[other_user])
        else:
            budget = budget_factory(members=[base_user, other_user])
        payload = self.PAYLOAD.copy()
        if with_owner:
            payload['owner'] = other_user.id
        api_client.force_authenticate(base_user)

        response = api_client.post(deposit_url(budget.id), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.filter(budget=budget).count() == 1
        deposit = Deposit.objects.get(id=response.data['id'])
        assert deposit.budget == budget
        if with_owner:
            assert deposit.owner.id == payload['owner']
        else:
            assert deposit.owner is None
        for key in payload:
            if key == 'owner':
                continue
            assert getattr(deposit, key) == payload[key]
        serializer = DepositSerializer(deposit)
        assert response.data == serializer.data

    def test_create_two_deposits_for_single_budget(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payloads prepared for two Deposits.
        WHEN: DepositViewSet called twice with POST by User belonging to Budget with valid payloads.
        THEN: Two Deposit objects created in database with given payloads.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload_1 = self.PAYLOAD.copy()
        payload_1['name'] = 'Deposit name 1'
        payload_2 = self.PAYLOAD.copy()
        payload_2['name'] = 'Deposit name 2'

        response_1 = api_client.post(deposit_url(budget.id), payload_1)
        response_2 = api_client.post(deposit_url(budget.id), payload_2)

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.filter(budget=budget).count() == 2
        for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
            deposit = Deposit.objects.get(id=response.data['id'])
            for key in payload:
                assert getattr(deposit, key) == payload[key]

    def test_create_same_deposit_for_two_budgets(self, api_client: APIClient, budget_factory: FactoryMetaClass):
        """
        GIVEN: Two Budget instances created in database. Valid payload prepared for two Deposits.
        WHEN: DepositViewSet called twice with POST by different Users belonging to two different
        Budgets with valid payload.
        THEN: Two Deposit objects created in database with given payload for separate Budgets.
        """
        payload = self.PAYLOAD.copy()
        budget_1 = budget_factory()
        budget_2 = budget_factory()

        api_client.force_authenticate(budget_1.owner)
        api_client.post(deposit_url(budget_1.id), payload)
        api_client.force_authenticate(budget_2.owner)
        api_client.post(deposit_url(budget_2.id), payload)

        assert Deposit.objects.all().count() == 2
        assert Deposit.objects.filter(budget=budget_1).count() == 1
        assert Deposit.objects.filter(budget=budget_2).count() == 1

    @pytest.mark.parametrize('field_name', ['name', 'description'])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for Deposit with field value too long.
        WHEN: DepositViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Deposit not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        max_length = Deposit._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * 'a'

        response = api_client.post(deposit_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data
        assert response.data[field_name][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not Deposit.objects.filter(budget=budget).exists()

    def test_error_name_already_used(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for Deposit.
        WHEN: DepositViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one Deposit created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()

        api_client.post(deposit_url(budget.id), payload)
        response = api_client.post(deposit_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == 'Deposit with given name already exists in Budget.'
        assert Deposit.objects.filter(budget=budget).count() == 1

    def test_is_active_default_value(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for Deposit.
        WHEN: DepositViewSet called with POST by User belonging to Budget with valid payload.
        THEN: Created HTTP 201 returned. Object created in database with default value for 'is_active' field.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        del payload['is_active']
        default_value = Deposit._meta.get_field('is_active').default

        response = api_client.post(deposit_url(budget.id), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.all().count() == 1
        assert Deposit.objects.filter(budget=budget).count() == 1
        assert response.data['is_active'] == default_value

    def test_error_create_deposit_for_not_accessible_budget(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for Deposit.
        WHEN: DepositViewSet called with POST by User not belonging to Budget with valid payload.
        THEN: Forbidden HTTP 403 returned. Object not created.
        """
        budget = budget_factory()
        api_client.force_authenticate(base_user)

        response = api_client.post(deposit_url(budget.id), self.PAYLOAD)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'
        assert not Deposit.objects.filter(budget=budget).exists()


@pytest.mark.django_db
class TestDepositApiDetail:
    """Tests for detail view on DepositViewSet."""

    @pytest.mark.parametrize('user_type', ['owner', 'member'])
    def test_get_deposit_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        user_type: str,
    ):
        """
        GIVEN: Deposit instance for Budget created in database.
        WHEN: DepositViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, Deposit details returned.
        """
        if user_type == 'owner':
            budget = budget_factory(owner=base_user)
        else:
            budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = deposit_detail_url(budget.id, deposit.id)

        response = api_client.get(url)
        serializer = DepositSerializer(deposit)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_deposit_details_unauthenticated(
        self, api_client: APIClient, base_user: AbstractUser, deposit_factory: FactoryMetaClass
    ):
        """
        GIVEN: Deposit instance for Budget created in database.
        WHEN: DepositViewSet detail view called without authentication.
        THEN: Unauthorized HTTP 401.
        """
        deposit = deposit_factory()
        url = deposit_detail_url(deposit.budget.id, deposit.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_details_from_not_accessible_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit instance for Budget created in database.
        WHEN: DepositViewSet detail view called by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        deposit = deposit_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)

        url = deposit_detail_url(deposit.budget.id, deposit.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


# @pytest.mark.django_db
# class TestDepositApiUpdate:
#     """Tests for update views on DepositViewSet."""
#
#     @pytest.mark.parametrize(
#         'param, value', [('name', 'New name'), ('description', 'New description'), ('is_active', True)]
#     )
#     def test_deposit_partial_update(
#         self, api_client: APIClient, base_user: Any, deposit_factory: FactoryMetaClass, param: str, value: Any
#     ):
#         """Test partial update of a Deposit"""
#         api_client.force_authenticate(base_user)
#         deposit = deposit_factory(user=base_user, name='Account', description='My account', is_active=False)
#         payload = {param: value}
#         url = deposit_detail_url(0, deposit.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         deposit.refresh_from_db()
#         assert getattr(deposit, param) == payload[param]
#
#     @pytest.mark.parametrize('param, value', [('name', 'Old account')])
#     def test_error_on_deposit_partial_update(
#         self, api_client: APIClient, base_user: Any, deposit_factory: FactoryMetaClass, param: str, value: Any
#     ):
#         """Test error on partial update of a Deposit."""
#         api_client.force_authenticate(base_user)
#         deposit_factory(user=base_user, name='Old account', description='My old account', is_active=True)
#         deposit = deposit_factory(user=base_user, name='New account', description='My new account', is_active=True)
#         old_value = getattr(deposit, param)
#         payload = {param: value}
#         url = deposit_detail_url(0, deposit.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         deposit.refresh_from_db()
#         assert getattr(deposit, param) == old_value
#
#     def test_deposit_full_update(self, api_client: APIClient, base_user: Any, deposit_factory: FactoryMetaClass):
#         """Test successful full update of a Deposit"""
#         api_client.force_authenticate(base_user)
#         payload_old = {
#             'name': 'Old account',
#             'description': 'My old account',
#             'is_active': False,
#         }
#         payload_new = {
#             'name': 'New account',
#             'description': 'My new account',
#             'is_active': True,
#         }
#         deposit = deposit_factory(user=base_user, **payload_old)
#         url = deposit_detail_url(0, deposit.id)
#
#         response = api_client.put(url, payload_new)
#
#         assert response.status_code == status.HTTP_200_OK
#         deposit.refresh_from_db()
#         for k, v in payload_new.items():
#             assert getattr(deposit, k) == v
#
#     @pytest.mark.parametrize(
#         'payload_new',
#         [
#             {'name': 'Old account', 'description': 'My new account', 'is_active': True},
#         ],
#     )
#     def test_error_on_deposit_full_update(
#         self, api_client: APIClient, base_user: Any, deposit_factory: FactoryMetaClass, payload_new: dict
#     ):
#         """Test error on full update of a Deposit."""
#         api_client.force_authenticate(base_user)
#         deposit_factory(user=base_user, name='Old account', description='My old account', is_active=True)
#         payload_old = {
#             'name': 'New account',
#             'description': 'My new account',
#             'is_active': True,
#         }
#
#         deposit = deposit_factory(user=base_user, **payload_old)
#         url = deposit_detail_url(0, deposit.id)
#
#         response = api_client.patch(url, payload_new)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         deposit.refresh_from_db()
#         for k, v in payload_old.items():
#             assert getattr(deposit, k) == v
#
# @pytest.mark.django_db
# class TestDepositApiDelete:
#     """Tests for delete Deposit on DepositViewSet."""
#     def test_delete_deposit(self, api_client: APIClient, base_user: Any, deposit_factory: FactoryMetaClass):
#         """Test deleting Deposit."""
#         api_client.force_authenticate(base_user)
#         deposit = deposit_factory(user=base_user)
#         url = deposit_detail_url(0, deposit.id)
#
#         assert Deposit.objects.all().count() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not Deposit.objects.all().exists()
