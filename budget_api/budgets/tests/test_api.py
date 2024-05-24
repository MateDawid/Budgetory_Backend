from datetime import date
from typing import Any

import pytest
from budgets.models import Budget, BudgetingPeriod
from budgets.serializers import BudgetingPeriodSerializer, BudgetSerializer
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

BUDGETS_URL = reverse('budgets:budget-list')
OWNED_BUDGETS_URL = reverse('budgets:budget-owned')
MEMBERED_BUDGETS_URL = reverse('budgets:budget-membered')


def budget_detail_url(budget_id):
    """Creates and returns Budget detail URL."""
    return reverse('budgets:budget-detail', args=[budget_id])


def periods_url(budget_id):
    """Creates and returns Budget BudgetingPeriods URL."""
    return reverse('budgets:period-list', args=[budget_id])


def period_detail_url(budget_id, period_id):
    """Creates and returns BudgetingPeriod detail URL."""
    return reverse('budgets:period-detail', args=[budget_id, period_id])


@pytest.mark.django_db
class TestBudgetApi:
    """Tests for BudgetViewSet."""

    def test_auth_required(self, api_client: APIClient):
        """Test auth is required to call endpoint."""
        res = api_client.get(BUDGETS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_objects_list(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """Test retrieving list of Budgets."""
        auth_user = user_factory()
        api_client.force_authenticate(auth_user)
        budget_factory(owner=auth_user, name='Budget 1', description='Some budget', currency='PLN')
        budget_factory(
            owner=user_factory(), name='Budget 2', description='Other budget', currency='eur', members=[auth_user]
        )

        response = api_client.get(BUDGETS_URL)

        budgets = Budget.objects.filter(Q(owner=auth_user) | Q(members=auth_user)).order_by('id').distinct()
        serializer = BudgetSerializer(budgets, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_object_list_limited_to_user(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """Test retrieved list of Budgets is limited to authenticated user."""
        auth_user = user_factory()
        budget_factory(owner=auth_user)
        budget_factory(owner=user_factory(), members=[auth_user])
        budget_factory()
        api_client.force_authenticate(auth_user)

        response = api_client.get(BUDGETS_URL)

        budgets = Budget.objects.filter(Q(owner=auth_user) | Q(members=auth_user)).order_by('id').distinct()
        serializer = BudgetSerializer(budgets, many=True)
        assert Budget.objects.all().count() == 3
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data
        assert len(response.data['results']) == budgets.count() == 2

    def test_retrieve_owned_list(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """Test retrieving list of Budgets owned by User."""
        auth_user = user_factory()
        api_client.force_authenticate(auth_user)
        budget_factory(owner=auth_user)
        budget_factory(owner=auth_user)
        budget_factory(owner=user_factory(), members=[auth_user])

        response = api_client.get(OWNED_BUDGETS_URL)

        owned_budgets = Budget.objects.filter(owner=auth_user).order_by('id').distinct()
        serializer = BudgetSerializer(owned_budgets, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_retrieve_membered_list(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """Test retrieving list of Budgets in which User is a member."""
        auth_user = user_factory()
        api_client.force_authenticate(auth_user)
        budget_factory(owner=auth_user)
        budget_factory(owner=user_factory(), members=[auth_user])
        budget_factory(owner=user_factory(), members=[auth_user, user_factory()])

        response = api_client.get(MEMBERED_BUDGETS_URL)

        membered_budgets = Budget.objects.filter(members=auth_user).order_by('id').distinct()
        serializer = BudgetSerializer(membered_budgets, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_create_single_object(self, api_client: APIClient, base_user: AbstractUser, user_factory: FactoryMetaClass):
        """Test creating single Budget."""
        api_client.force_authenticate(base_user)
        payload = {
            'name': 'Budget 1',
            'description': 'Some budget',
            'currency': 'PLN',
            'members': [user_factory().id, user_factory().id],
        }

        response = api_client.post(BUDGETS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Budget.objects.filter(owner=base_user).count() == 1
        budget = Budget.objects.get(id=response.data['id'])
        for key in payload:
            if key == 'members':
                members = getattr(budget, key)
                assert members.count() == len(payload[key])
                for member_id in payload[key]:
                    assert members.filter(id=member_id).exists()
            else:
                assert getattr(budget, key) == payload[key]
        serializer = BudgetSerializer(budget)
        assert response.data == serializer.data

    def test_create_two_objects_by_one_user(
        self, api_client: APIClient, base_user: AbstractUser, user_factory: FactoryMetaClass
    ):
        """Test creating two valid Budgets by single User."""
        api_client.force_authenticate(base_user)
        payload_1 = {
            'name': 'Budget 1',
            'description': 'Some budget',
            'currency': 'PLN',
            'members': [user_factory().id, user_factory().id],
        }
        payload_2 = {'name': 'Budget 2', 'description': 'Another budget', 'currency': 'eur', 'members': []}

        response_1 = api_client.post(BUDGETS_URL, payload_1)
        response_2 = api_client.post(BUDGETS_URL, payload_2)

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED
        assert Budget.objects.filter(owner=base_user).count() == 2
        for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
            budget = Budget.objects.get(id=response.data['id'])
            for key in payload:
                if key == 'members':
                    members = getattr(budget, key)
                    assert members.count() == len(payload[key])
                    for member_id in payload[key]:
                        assert members.filter(id=member_id).exists()
                else:
                    assert getattr(budget, key) == payload[key]

    def test_create_same_object_by_two_users(self, api_client: APIClient, user_factory: AbstractUser):
        """Test creating Budget with the same params by two users."""
        payload = {'name': 'Budget', 'description': 'Some budget', 'currency': 'eur', 'members': []}
        user_1 = user_factory()
        api_client.force_authenticate(user_1)
        api_client.post(BUDGETS_URL, payload)

        user_2 = user_factory()
        api_client.force_authenticate(user_2)
        api_client.post(BUDGETS_URL, payload)

        assert Budget.objects.all().count() == 2
        assert Budget.objects.filter(owner=user_1).count() == 1
        assert Budget.objects.filter(owner=user_2).count() == 1

    def test_error_name_too_long(self, api_client: APIClient, base_user: AbstractUser, user_factory: AbstractUser):
        """Test error on creating Budget with name too long."""
        api_client.force_authenticate(base_user)
        max_length = Budget._meta.get_field('name').max_length
        payload = {
            'name': (max_length + 1) * 'a',
            'description': 'Some budget',
            'currency': 'PLN',
            'members': [user_factory().id, user_factory().id],
        }

        response = api_client.post(BUDGETS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not Budget.objects.filter(owner=base_user).exists()

    def test_error_name_already_used(self, api_client: APIClient, base_user: AbstractUser):
        """Test error on creating BudgetingPeriod with already used name by the same user."""
        api_client.force_authenticate(base_user)
        payload = {'name': 'Budget', 'description': 'Some budget', 'currency': 'eur'}
        Budget.objects.create(owner=base_user, **payload)

        response = api_client.post(BUDGETS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'User already owns Budget with name "{payload["name"]}".'
        assert Budget.objects.filter(owner=base_user).count() == 1

    def test_get_object_details(self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass):
        """Test get Budget details."""
        api_client.force_authenticate(base_user)
        budget = budget_factory(owner=base_user)
        url = budget_detail_url(budget.id)

        response = api_client.get(url)
        serializer = BudgetSerializer(budget)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_object_details_unauthenticated(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """Test error on getting Budget details being unauthenticated."""
        budget = budget_factory(owner=base_user)
        url = budget_detail_url(budget.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_other_user_object_details(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """Test error on getting other user's Budget details."""
        user_1 = user_factory()
        user_2 = user_factory()
        budget = budget_factory(owner=user_1)
        api_client.force_authenticate(user_2)

        url = budget_detail_url(budget.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'param, value',
        [('name', 'New name'), ('description', 'New description'), ('currency', 'PLN')],
    )
    def test_object_partial_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """Test partial update of a Budget"""
        user_factory()
        user_factory()
        api_client.force_authenticate(base_user)
        payload = {'name': 'Budget', 'description': 'Some budget', 'currency': 'eur'}
        budget = budget_factory(owner=base_user, **payload)
        update_payload = {param: value}
        url = budget_detail_url(budget.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        budget.refresh_from_db()

    def test_partial_update_with_members(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
    ):
        """Test partial update of Budget members."""
        user_1 = user_factory()
        user_2 = user_factory()
        api_client.force_authenticate(base_user)
        payload = {'name': 'Budget', 'description': 'Some budget', 'currency': 'eur', 'members': [user_1.id]}
        budget = budget_factory(owner=base_user, **payload)
        update_payload = {'members': [user_1.id, user_2.id]}
        url = budget_detail_url(budget.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        budget.refresh_from_db()
        assert list(budget.members.all().values_list('id', flat=True)) == update_payload['members']

    @pytest.mark.parametrize(
        'param, value',
        [
            ('name', (Budget._meta.get_field('name').max_length + 1) * 'A'),
            ('name', 'Old budget'),
            ('currency', (Budget._meta.get_field('currency').max_length + 1) * 'A'),
        ],
    )
    def test_error_on_object_partial_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """Test error on partial update of a Budget."""
        user_factory()
        api_client.force_authenticate(base_user)
        old_payload = {'name': 'Old budget', 'description': 'Some budget', 'currency': 'eur'}
        budget_factory(owner=base_user, **old_payload)
        new_payload = {'name': 'New budget', 'description': 'Some budget', 'currency': 'eur'}
        budget = budget_factory(owner=base_user, **new_payload)
        old_value = getattr(budget, param)
        payload = {param: value}
        url = budget_detail_url(budget.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        budget.refresh_from_db()
        assert getattr(budget, param) == old_value

    def test_owner_unchangeable(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
    ):
        """Test owner is not changed after partial updating a Budget."""
        other_user = user_factory()
        api_client.force_authenticate(base_user)
        budget = budget_factory(owner=base_user)

        payload = {'owner': other_user.id}
        url = budget_detail_url(budget.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        budget.refresh_from_db()
        assert budget.owner == base_user

    def test_object_full_update(self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass):
        """Test successful full update of a BudgetingPeriod"""
        api_client.force_authenticate(base_user)
        old_payload = {'name': 'Old budget', 'description': 'Some budget', 'currency': 'eur'}
        new_payload = {'name': 'New budget', 'description': 'New description', 'currency': 'pln'}
        budget = budget_factory(owner=base_user, **old_payload)
        url = budget_detail_url(budget.id)

        response = api_client.put(url, new_payload)

        assert response.status_code == status.HTTP_200_OK
        budget.refresh_from_db()
        for k, v in new_payload.items():
            assert getattr(budget, k) == v

    def test_full_update_with_members(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
    ):
        """Test full update of Budget members."""
        user_1 = user_factory()
        user_2 = user_factory()
        api_client.force_authenticate(base_user)
        old_payload = {'name': 'Old budget', 'description': 'Some budget', 'members': [user_1.id], 'currency': 'eur'}
        new_payload = {
            'name': 'New budget',
            'description': 'New description',
            'members': [user_2.id],
            'currency': 'pln',
        }
        budget = budget_factory(owner=base_user, **old_payload)
        url = budget_detail_url(budget.id)

        response = api_client.put(url, new_payload)

        assert response.status_code == status.HTTP_200_OK
        budget.refresh_from_db()
        assert list(budget.members.all().values_list('id', flat=True)) == new_payload['members']

    @pytest.mark.parametrize(
        'new_payload',
        [
            {
                'name': (Budget._meta.get_field('name').max_length + 1) * 'A',
                'description': 'New description',
                'currency': 'pln',
            },
            {'name': 'Existing budget', 'description': 'New description', 'currency': 'pln'},
            {
                'name': 'New budget',
                'description': 'New description',
                'currency': (Budget._meta.get_field('currency').max_length + 1) * 'A',
            },
        ],
    )
    def test_error_on_object_full_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        new_payload: dict,
    ):
        """Test error on full update of a Budget."""
        api_client.force_authenticate(base_user)
        existing_payload = {'name': 'Existing budget', 'description': 'Some budget', 'currency': 'eur'}
        budget_factory(owner=base_user, **existing_payload)
        old_payload = {'name': 'Old budget', 'description': 'Some budget', 'currency': 'eur'}

        budget = budget_factory(owner=base_user, **old_payload)
        url = budget_detail_url(budget.id)

        response = api_client.patch(url, new_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        budget.refresh_from_db()
        for k, v in old_payload.items():
            assert getattr(budget, k) == v

    def test_delete_object(self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass):
        """Test deleting Budget."""
        api_client.force_authenticate(base_user)
        budget = budget_factory(owner=base_user)
        url = budget_detail_url(budget.id)

        assert Budget.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Budget.objects.all().exists()


@pytest.mark.django_db
class TestBudgetingPeriodApiList:
    """Tests for BudgetingPeriodViewSet list view."""

    def test_auth_required(self, budget: Budget, api_client: APIClient):
        """
        GIVEN: Budget model instance in database created.
        WHEN: BudgetingPeriodViewSet list view called without authentication.
        THEN: Unauthorized HTTP status returned.
        """
        url = periods_url(budget.id)

        res = api_client.get(url)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_periods_list_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two BudgetingPeriods for Budget in database created.
        WHEN: BudgetingPeriodViewSet list view for Budget id called by authenticated Budget owner.
        THEN: List of BudgetingPeriods for given Budget id sorted from newest to oldest returned.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        budgeting_period_factory(
            budget=budget, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31), is_active=False
        )
        budgeting_period_factory(budget=budget, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28), is_active=True)
        url = periods_url(budget.id)

        response = api_client.get(url)

        periods = BudgetingPeriod.objects.filter(budget=budget).order_by('-date_start')
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(serializer.data) == periods.count() == 2
        assert response.data['results'] == serializer.data

    def test_retrieve_periods_list_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two BudgetingPeriods for Budget in database created.
        WHEN: BudgetingPeriodViewSet list view for Budget id called by authenticated Budget member.
        THEN: List of BudgetingPeriods for given Budget id sorted from newest to oldest returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        budgeting_period_factory(
            budget=budget, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31), is_active=False
        )
        budgeting_period_factory(budget=budget, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28), is_active=True)
        url = periods_url(budget.id)

        response = api_client.get(url)

        periods = BudgetingPeriod.objects.filter(budget=budget).order_by('-date_start')
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(serializer.data) == periods.count() == 2
        assert response.data['results'] == serializer.data

    def test_periods_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two BudgetingPeriods for two different Budgets in database created.
        WHEN: BudgetingPeriodViewSet list view for Budget id called by authenticated User.
        THEN: List of BudgetingPeriods containing only declared Budget periods returned.
        """
        # Other period
        budgeting_period_factory()
        # Auth User period
        budget = budget_factory(owner=base_user)
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = periods_url(budget.id)

        response = api_client.get(url)

        periods = BudgetingPeriod.objects.filter(budget=budget)
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert BudgetingPeriod.objects.all().count() == 2
        assert len(response.data['results']) == len(serializer.data) == periods.count() == 1
        assert periods.first() == period
        assert response.data['results'] == serializer.data


@pytest.mark.django_db
class TestBudgetingPeriodApiCreate:
    """Tests for creating BudgetingPeriod via BudgetingPeriodViewSet."""

    def test_create_single_period_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view for Budget id called by authenticated Budget owner by POST with
        valid data.
        THEN: BudgetingPeriod for Budget created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date(2023, 1, 1), 'date_end': date(2023, 1, 31)}
        url = periods_url(budget.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1
        period = BudgetingPeriod.objects.get(id=response.data['id'])
        for key in payload:
            assert getattr(period, key) == payload[key]
        serializer = BudgetingPeriodSerializer(period)
        assert response.data == serializer.data

    def test_create_single_period_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view for Budget id called by Budget member by POST with valid data.
        THEN: BudgetingPeriod for Budget created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date(2023, 1, 1), 'date_end': date(2023, 1, 31)}
        url = periods_url(budget.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1
        period = BudgetingPeriod.objects.get(id=response.data['id'])
        for key in payload:
            assert getattr(period, key) == payload[key]
        serializer = BudgetingPeriodSerializer(period)
        assert response.data == serializer.data

    def test_create_two_periods_for_one_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view for Budget id called by authenticated User by POST
        with valid data two times.
        THEN: Two BudgetingPeriod for Budget created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload_1 = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        payload_2 = {
            'name': '2023_02',
            'date_start': date(2023, 2, 1),
            'date_end': date(2023, 2, 28),
        }
        url = periods_url(budget.id)

        response_1 = api_client.post(url, payload_1)
        response_2 = api_client.post(url, payload_2)

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 2
        for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
            period = BudgetingPeriod.objects.get(id=response.data['id'])
            for key in payload:
                assert getattr(period, key) == payload[key]

    def test_create_same_period_for_two_budgets(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Two Budgets in database created.
        WHEN: BudgetingPeriodViewSet list view called for two Budgets by authenticated User by POST with valid data.
        THEN: Two BudgetingPeriod, every for different Budget created in database.
        """
        payload = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        api_client.force_authenticate(base_user)
        budget_1 = budget_factory(owner=base_user)
        url = periods_url(budget_1.id)
        api_client.post(url, payload)
        budget_2 = budget_factory(owner=base_user)
        url = periods_url(budget_2.id)
        api_client.post(url, payload)

        all_periods_queryset = BudgetingPeriod.objects.all()
        assert all_periods_queryset.count() == 2
        for budget in (budget_1, budget_2):
            budget_periods_queryset = all_periods_queryset.filter(budget=budget)
            assert budget_periods_queryset.count() == 1

    def test_error_name_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called for Budget by authenticated User by POST with name
        too long in passed data.
        THEN: Bad request 400 returned, no object in database created.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        max_length = BudgetingPeriod._meta.get_field('name').max_length
        payload = {
            'name': (max_length + 1) * 'a',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        url = periods_url(budget.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not BudgetingPeriod.objects.filter(budget=budget).exists()

    def test_error_name_already_used(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: BudgetingPeriod for Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called for Budget by authenticated User by POST with name already used
        for existing BudgetingPeriod in passed data.
        THEN: Bad request 400 returned, no object in database created.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 2),
        }
        BudgetingPeriod.objects.create(budget=budget, **payload)
        payload['date_start'] = date(2023, 1, 3)
        payload['date_end'] = date(2023, 1, 4)
        url = periods_url(budget.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'Period with name "{payload["name"]}" already exists in Budget.'
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1

    def test_create_active_period_successfully(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called twice for Budget by authenticated User by POST to create active
        and inactive BudgetingPeriods.
        THEN: Two BudgetingPeriods for Budget in database create - one active, one inactive.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload_inactive = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': False,
        }
        payload_active = {
            'name': '2023_02',
            'date_start': date(2023, 2, 1),
            'date_end': date(2023, 2, 28),
            'is_active': True,
        }
        url = periods_url(budget.id)

        response_inactive = api_client.post(url, payload_inactive)
        response_active = api_client.post(url, payload_active)

        assert BudgetingPeriod.objects.all().count() == 2
        budget_periods = BudgetingPeriod.objects.filter(budget=budget)
        assert budget_periods.count() == 2
        for response, payload in [(response_inactive, payload_inactive), (response_active, payload_active)]:
            assert response.status_code == status.HTTP_201_CREATED
            period = budget_periods.get(id=response.data['id'])
            assert period.is_active == payload['is_active']

    def test_error_create_period_when_is_active_set_already(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Active BudgetingPeriod for Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called for Budget by authenticated User by POST
        to create active BudgetingPeriod.
        THEN: Bad request 400 returned, no object in database created.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload_1 = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }
        active_period = BudgetingPeriod.objects.create(budget=budget, **payload_1)
        payload_2 = {
            'name': '2023_02',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }
        url = periods_url(budget.id)

        response = api_client.post(url, payload_2)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'is_active' in response.data
        assert response.data['is_active'][0] == 'Active period already exists in Budget.'
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1
        assert BudgetingPeriod.objects.filter(budget=budget).first() == active_period

    def test_is_active_default_value(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called for Budget by authenticated User by POST to create
        BudgetingPeriod without declaring if it's active or not.
        THEN: BudgetingPeriod for Budget in database created with 'is_active' set to False by default.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = {
            'name': '2023_02',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': '',
        }
        url = periods_url(budget.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert BudgetingPeriod.objects.all().count() == 1
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1
        assert response.data['is_active'] is False

    @pytest.mark.parametrize('date_start, date_end', (('', date.today()), (date.today(), ''), ('', '')))
    def test_error_date_blank(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        date_start: date | str,
        date_end: date | str,
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called for Budget by authenticated User by POST to create
        BudgetingPeriod with one of or both dates blank.
        THEN: Bad request 400 returned, no object in database created.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date_start, 'date_end': date_end, 'is_active': False}
        url = periods_url(budget.id)
        error_message = 'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'date_start' in response.data or 'date_end' in response.data
        assert (
            response.data.get('date_start', [''])[0] == error_message
            or response.data.get('date_end', [''])[0] == error_message
        )
        assert not BudgetingPeriod.objects.filter(budget=budget).exists()

    def test_error_date_end_before_date_start(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called for Budget by authenticated User by POST to create
        BudgetingPeriod with date_end before date_start.
        THEN: Bad request 400 returned, no object in database created.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date(2023, 5, 1), 'date_end': date(2023, 4, 30), 'is_active': False}
        url = periods_url(budget.id)

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert response.data['non_field_errors'][0] == 'Start date should be earlier than end date.'
        assert not BudgetingPeriod.objects.filter(budget=budget).exists()

    @pytest.mark.parametrize(
        'date_start, date_end',
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
    def test_error_date_invalid(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        date_start: date,
        date_end: date,
    ):
        """
        GIVEN: Two BudgetingPeriods for Budget in database created.
        WHEN: BudgetingPeriodViewSet list view called for Budget by authenticated User by POST to create
        BudgetingPeriod with dates colliding with existing BudgetingPeriods.
        THEN: Bad request 400 returned, no object in database created.
        """
        budget = budget_factory(owner=base_user)
        payload_1 = {
            'name': '2023_06',
            'date_start': date(2023, 6, 1),
            'date_end': date(2023, 6, 30),
        }
        payload_2 = {
            'name': '2023_07',
            'date_start': date(2023, 7, 1),
            'date_end': date(2023, 7, 31),
        }
        payload_invalid = {
            'name': 'invalid',
            'date_start': date_start,
            'date_end': date_end,
        }
        BudgetingPeriod.objects.create(budget=budget, **payload_1)
        BudgetingPeriod.objects.create(budget=budget, **payload_2)
        api_client.force_authenticate(base_user)
        url = periods_url(budget.id)

        response = api_client.post(url, payload_invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert (
            response.data['non_field_errors'][0] == 'Budgeting period date range collides with other period in Budget.'
        )
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 2


@pytest.mark.django_db
class TestBudgetingPeriodApiDetail:
    """Tests for detail view in BudgetingPeriodViewSet."""

    def test_get_period_details_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet detail view called for BudgetingPeriod by authenticated User (owner of Budget).
        THEN: BudgetingPeriod details returned.
        """
        budget = budget_factory(owner=base_user)
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = period_detail_url(budget.id, period.id)

        response = api_client.get(url)
        serializer = BudgetingPeriodSerializer(period)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_get_period_details_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet detail view called for BudgetingPeriod by authenticated User (member of Budget).
        THEN: BudgetingPeriod details returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = period_detail_url(budget.id, period.id)

        response = api_client.get(url)
        serializer = BudgetingPeriodSerializer(period)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_period_details_unauthenticated(
        self, api_client: APIClient, budgeting_period_factory: FactoryMetaClass
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet detail view called for BudgetingPeriod without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        period = budgeting_period_factory()
        url = period_detail_url(period.budget.id, period.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_other_user_period_details(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet detail view called for BudgetingPeriod by authenticated User (not Budget owner
        nor member).
        THEN: Forbidden HTTP 403 returned.
        """
        user_1 = user_factory()
        user_2 = user_factory()
        period = budgeting_period_factory(budget=budget_factory(owner=user_1))
        api_client.force_authenticate(user_2)

        url = period_detail_url(period.budget.id, period.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestBudgetingPeriodApiPatch:
    """Tests for partial update BudgetingPeriod via BudgetingPeriodViewSet."""

    @pytest.mark.parametrize(
        'param, value', [('date_start', date(2024, 1, 2)), ('date_end', date(2024, 1, 30)), ('is_active', True)]
    )
    def test_period_partial_update_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget owner) by
        PATCH with valid data.
        THEN: BudgetingPeriod updated in database.
        """
        api_client.force_authenticate(base_user)
        period = budgeting_period_factory(
            budget=budget_factory(owner=base_user),
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 31),
            is_active=False,
        )
        payload = {param: value}
        url = period_detail_url(period.budget.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        assert getattr(period, param) == payload[param]

    @pytest.mark.parametrize(
        'param, value', [('date_start', date(2024, 1, 2)), ('date_end', date(2024, 1, 30)), ('is_active', True)]
    )
    def test_period_partial_update_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget member) by
        PATCH with valid data.
        THEN: BudgetingPeriod updated in database.
        """
        api_client.force_authenticate(base_user)
        period = budgeting_period_factory(
            budget=budget_factory(members=[base_user]),
            date_start=date(2024, 1, 1),
            date_end=date(2024, 1, 31),
            is_active=False,
        )
        payload = {param: value}
        url = period_detail_url(period.budget.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        assert getattr(period, param) == payload[param]

    @pytest.mark.parametrize(
        'param, value', [('date_start', date(2023, 12, 31)), ('date_end', date(2024, 2, 1)), ('is_active', True)]
    )
    def test_error_on_period_partial_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget owner) by
        PATCH with invalid data.
        THEN: Bad request HTTP 400 returned.
        """
        api_client.force_authenticate(base_user)
        budget = budget_factory(owner=base_user)
        budgeting_period_factory(budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True)
        period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), is_active=False
        )
        old_value = getattr(period, param)
        payload = {param: value}
        url = period_detail_url(budget.id, period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        assert getattr(period, param) == old_value


@pytest.mark.django_db
class TestBudgetingPeriodApiPut:
    """Tests for full update BudgetingPeriod via BudgetingPeriodViewSet."""

    def test_period_full_update_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget owner) by
        PUT with valid data.
        THEN: BudgetingPeriod updated in database.
        """
        api_client.force_authenticate(base_user)
        payload_old = {
            'name': '2023_06',
            'date_start': date(2023, 6, 1),
            'date_end': date(2023, 6, 30),
            'is_active': False,
        }
        payload_new = {
            'name': '2023_07',
            'date_start': date(2023, 7, 1),
            'date_end': date(2023, 7, 31),
            'is_active': True,
        }
        period = budgeting_period_factory(budget=budget_factory(owner=base_user), **payload_old)
        url = period_detail_url(period.budget.id, period.id)

        response = api_client.put(url, payload_new)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        for k, v in payload_new.items():
            assert getattr(period, k) == v

    def test_period_full_update_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget member) by
        PUT with valid data.
        THEN: BudgetingPeriod updated in database.
        """
        api_client.force_authenticate(base_user)
        payload_old = {
            'name': '2023_06',
            'date_start': date(2023, 6, 1),
            'date_end': date(2023, 6, 30),
            'is_active': False,
        }
        payload_new = {
            'name': '2023_07',
            'date_start': date(2023, 7, 1),
            'date_end': date(2023, 7, 31),
            'is_active': True,
        }
        period = budgeting_period_factory(budget=budget_factory(members=[base_user]), **payload_old)
        url = period_detail_url(period.budget.id, period.id)

        response = api_client.put(url, payload_new)

        assert response.status_code == status.HTTP_200_OK
        period.refresh_from_db()
        for k, v in payload_new.items():
            assert getattr(period, k) == v

    @pytest.mark.parametrize(
        'payload_new',
        [
            {'name': '2024_01', 'date_start': date(2024, 2, 1), 'date_end': date(2024, 2, 29), 'is_active': False},
            {'name': '2024_02', 'date_start': date(2024, 1, 31), 'date_end': date(2024, 2, 29), 'is_active': False},
            {'name': '2024_02', 'date_start': date(2024, 2, 1), 'date_end': date(2024, 2, 29), 'is_active': True},
        ],
    )
    def test_error_on_period_full_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        payload_new: dict,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget owner) by
        PUT with invalid data.
        THEN: Bad request HTTP 400 returned.
        """
        api_client.force_authenticate(base_user)
        budget = budget_factory(owner=base_user)
        budgeting_period_factory(
            budget=budget, name='2024_01', date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True
        )
        payload_old = {
            'name': '2024_02',
            'date_start': date(2024, 2, 1),
            'date_end': date(2024, 2, 29),
            'is_active': False,
        }
        period = budgeting_period_factory(budget=budget, **payload_old)
        url = period_detail_url(budget.id, period.id)

        response = api_client.patch(url, payload_new)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        for k, v in payload_old.items():
            assert getattr(period, k) == v


@pytest.mark.django_db
class TestBudgetingPeriodApiDelete:
    """Tests for delete BudgetingPeriod via BudgetingPeriodViewSet."""

    def test_delete_period_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget owner)
        by DELETE.
        THEN: BudgetingPeriod deleted from database.
        """
        api_client.force_authenticate(base_user)
        period = budgeting_period_factory(budget=budget_factory(owner=base_user))
        url = period_detail_url(period.budget.id, period.id)

        assert BudgetingPeriod.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BudgetingPeriod.objects.all().exists()

    def test_delete_period_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (Budget member)
        by DELETE.
        THEN: BudgetingPeriod deleted from database.
        """
        api_client.force_authenticate(base_user)
        period = budgeting_period_factory(budget=budget_factory(members=[base_user]))
        url = period_detail_url(period.budget.id, period.id)

        assert BudgetingPeriod.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BudgetingPeriod.objects.all().exists()

    def test_error_delete_not_accessible_period(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod created in database.
        WHEN: BudgetingPeriodViewSet list view called for BudgetingPeriod by authenticated User (not Budget owner
        nor member) by DELETE.
        THEN: Forbidden HTTP 403 returned, BudgetingPeriod not deleted.
        """
        period = budgeting_period_factory(budget=budget_factory(owner=user_factory()))
        url = period_detail_url(period.budget.id, period.id)
        api_client.force_authenticate(user_factory())

        assert BudgetingPeriod.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert BudgetingPeriod.objects.filter(id=period.id).exists()
