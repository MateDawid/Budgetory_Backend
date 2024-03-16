from datetime import date
from typing import Optional

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
PERIODS_URL = reverse('budgets:budgetingperiod-list')


def budget_detail_url(budget_id):
    """Creates and returns Budget detail URL."""
    return reverse('budgets:budget-detail', args=[budget_id])


def period_detail_url(period_id):
    """Creates and returns BudgetingPeriod detail URL."""
    return reverse('budgets:budgetingperiod-detail', args=[period_id])


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
        assert not BudgetingPeriod.objects.filter(user=base_user).exists()


#     def test_error_name_already_used(self, api_client: APIClient, base_user: AbstractUser):
#         """Test error on creating BudgetingPeriod with already used name by the same user."""
#         api_client.force_authenticate(base_user)
#         payload = {
#             'name': '2023_01',
#             'date_start': date(2023, 1, 1),
#             'date_end': date(2023, 1, 2),
#         }
#         BudgetingPeriod.objects.create(user=base_user, **payload)
#         payload['date_start'] = date(2023, 1, 3)
#         payload['date_end'] = date(2023, 1, 4)
#
#         response = api_client.post(PERIODS_URL, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'name' in response.data
#         assert response.data['name'][0] == f"Users period with name {payload['name']} already exists."
#         assert BudgetingPeriod.objects.filter(user=base_user).count() == 1
#
#     def test_create_active_period_successfully(self, api_client: APIClient, base_user: AbstractUser):
#         """Test creating BudgetingPeriod with is_active=True successfully."""
#         api_client.force_authenticate(base_user)
#         payload_inactive = {
#             'name': '2023_01',
#             'date_start': date(2023, 1, 1),
#             'date_end': date(2023, 1, 31),
#             'is_active': False,
#         }
#         payload_active = {
#             'name': '2023_02',
#             'date_start': date(2023, 2, 1),
#             'date_end': date(2023, 2, 28),
#             'is_active': True,
#         }
#
#         response_inactive = api_client.post(PERIODS_URL, payload_inactive)
#         response_active = api_client.post(PERIODS_URL, payload_active)
#
#         assert BudgetingPeriod.objects.all().count() == 2
#         assert BudgetingPeriod.objects.filter(user=base_user).count() == 2
#         for response, payload in [(response_inactive, payload_inactive), (response_active, payload_active)]:
#             assert response.status_code == status.HTTP_201_CREATED
#             period = BudgetingPeriod.objects.get(id=response.data['id'])
#             assert period.is_active == payload['is_active']
#
#     def test_error_create_period_when_is_active_set_already(self, api_client: APIClient, base_user: AbstractUser):
#         """Test error on creating new BudgetingPeriod with is_active=True,
#         when another user's period active already."""
#         api_client.force_authenticate(base_user)
#         payload_1 = {
#             'name': '2023_01',
#             'date_start': date(2023, 1, 1),
#             'date_end': date(2023, 1, 31),
#             'is_active': True,
#         }
#         active_period = BudgetingPeriod.objects.create(user=base_user, **payload_1)
#         payload_2 = {
#             'name': '2023_02',
#             'date_start': date(2023, 1, 1),
#             'date_end': date(2023, 1, 31),
#             'is_active': True,
#         }
#
#         response = api_client.post(PERIODS_URL, payload_2)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'is_active' in response.data
#         assert response.data['is_active'][0] == 'User already has active budgeting period.'
#         assert BudgetingPeriod.objects.filter(user=base_user).count() == 1
#         assert BudgetingPeriod.objects.filter(user=base_user).first() == active_period
#
#     def test_is_active_default_value(self, api_client: APIClient, base_user: AbstractUser):
#         """Test creating BudgetingPeriod without passing is_active ends with default False value."""
#         api_client.force_authenticate(base_user)
#         payload = {
#             'name': '2023_02',
#             'date_start': date(2023, 1, 1),
#             'date_end': date(2023, 1, 31),
#             'is_active': '',
#         }
#
#         response = api_client.post(PERIODS_URL, payload)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         assert BudgetingPeriod.objects.all().count() == 1
#         assert BudgetingPeriod.objects.filter(user=base_user).count() == 1
#         assert response.data['is_active'] is False
#
#     @pytest.mark.parametrize('date_start, date_end', (('', date.today()), (date.today(), ''), ('', '')))
#     def test_error_date_blank(
#         self, api_client: APIClient, base_user: AbstractUser, date_start: Optional[date], date_end: Optional[date]
#     ):
#         """Test error on creating BudgetingPeriod with date_start or date_end blank."""
#         api_client.force_authenticate(base_user)
#         payload = {'name': '2023_01', 'date_start': date_start, 'date_end': date_end, 'is_active': False}
#         error_message = 'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'
#
#         response = api_client.post(PERIODS_URL, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'date_start' in response.data or 'date_end' in response.data
#         assert (
#             response.data.get('date_start', [''])[0] == error_message
#             or response.data.get('date_end', [''])[0] == error_message
#         )
#         assert not BudgetingPeriod.objects.filter(user=base_user).exists()
#
#     def test_error_date_end_before_date_start(self, api_client: APIClient, base_user: AbstractUser):
#         """Test error on creating BudgetingPeriod with date_end earlier than date_start."""
#         api_client.force_authenticate(base_user)
#         payload = {'name': '2023_01', 'date_start': date(2023, 5, 1), 'date_end': date(2023, 4, 30),
#         'is_active': False}
#
#         response = api_client.post(PERIODS_URL, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Start date should be earlier than end date.'
#         assert not BudgetingPeriod.objects.filter(user=base_user).exists()
#
#     @pytest.mark.parametrize(
#         'date_start, date_end',
#         (
#             # Date start before first existing period
#             (date(2023, 5, 1), date(2023, 6, 1)),
#             (date(2023, 5, 1), date(2023, 6, 15)),
#             (date(2023, 5, 1), date(2023, 6, 30)),
#             (date(2023, 5, 1), date(2023, 7, 1)),
#             (date(2023, 5, 1), date(2023, 7, 15)),
#             (date(2023, 5, 1), date(2023, 7, 31)),
#             (date(2023, 5, 1), date(2023, 8, 1)),
#             # Date start same as in first existing period
#             (date(2023, 6, 1), date(2023, 6, 15)),
#             (date(2023, 6, 1), date(2023, 6, 30)),
#             (date(2023, 6, 1), date(2023, 7, 1)),
#             (date(2023, 6, 1), date(2023, 7, 15)),
#             (date(2023, 6, 1), date(2023, 7, 31)),
#             (date(2023, 6, 1), date(2023, 8, 1)),
#             # Date start between first existing period daterange
#             (date(2023, 6, 15), date(2023, 6, 30)),
#             (date(2023, 6, 15), date(2023, 7, 1)),
#             (date(2023, 6, 15), date(2023, 7, 15)),
#             (date(2023, 6, 15), date(2023, 7, 31)),
#             (date(2023, 6, 15), date(2023, 8, 1)),
#             # Date start same as first existing period's end date
#             (date(2023, 6, 30), date(2023, 7, 1)),
#             (date(2023, 6, 30), date(2023, 7, 15)),
#             (date(2023, 6, 30), date(2023, 7, 31)),
#             (date(2023, 6, 30), date(2023, 8, 1)),
#             # Date start same as in second existing period
#             (date(2023, 7, 1), date(2023, 7, 15)),
#             (date(2023, 7, 1), date(2023, 7, 31)),
#             (date(2023, 7, 1), date(2023, 8, 1)),
#             # Date start between second existing period daterange
#             (date(2023, 7, 15), date(2023, 7, 31)),
#             # Date start same as second existing period's end date
#             (date(2023, 7, 31), date(2023, 8, 1)),
#         ),
#     )
#     def test_error_date_invalid(self, api_client: APIClient, base_user: AbstractUser,
#     date_start: date, date_end: date):
#         """Test error on creating BudgetingPeriod with invalid dates."""
#         api_client.force_authenticate(base_user)
#         payload_1 = {
#             'name': '2023_06',
#             'date_start': date(2023, 6, 1),
#             'date_end': date(2023, 6, 30),
#         }
#         payload_2 = {
#             'name': '2023_07',
#             'date_start': date(2023, 7, 1),
#             'date_end': date(2023, 7, 31),
#         }
#         payload_invalid = {
#             'name': 'invalid',
#             'date_start': date_start,
#             'date_end': date_end,
#         }
#         BudgetingPeriod.objects.create(user=base_user, **payload_1)
#         BudgetingPeriod.objects.create(user=base_user, **payload_2)
#
#         response = api_client.post(PERIODS_URL, payload_invalid)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0]
#             == "Budgeting period date range collides with other user's budgeting periods."
#         )
#         assert BudgetingPeriod.objects.filter(user=base_user).count() == 2
#
#     def test_get_period_details(
#         self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
#     ):
#         """Test get BudgetingPeriod details."""
#         api_client.force_authenticate(base_user)
#         period = budgeting_period_factory(user=base_user)
#         url = period_detail_url(period.id)
#
#         response = api_client.get(url)
#         serializer = BudgetingPeriodSerializer(period)
#
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data == serializer.data
#
#     def test_error_get_period_details_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
#     ):
#         """Test error on getting BudgetingPeriod details being unauthenticated."""
#         period = budgeting_period_factory(user=base_user)
#         url = period_detail_url(period.id)
#
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_get_other_user_period_details(
#         self, api_client: APIClient, user_factory: FactoryMetaClass, budgeting_period_factory: FactoryMetaClass
#     ):
#         """Test error on getting other user's BudgetingPeriod details."""
#         user_1 = user_factory()
#         user_2 = user_factory()
#         period = budgeting_period_factory(user=user_1)
#         api_client.force_authenticate(user_2)
#
#         url = period_detail_url(period.id)
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_404_NOT_FOUND
#
#     @pytest.mark.parametrize(
#         'param, value', [('date_start', date(2024, 1, 2)), ('date_end', date(2024, 1, 30)), ('is_active', True)]
#     )
#     def test_period_partial_update(
#         self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass, param: str,
#         value: AbstractUser
#     ):
#         """Test partial update of a BudgetingPeriod"""
#         api_client.force_authenticate(base_user)
#         period = budgeting_period_factory(
#             user=base_user, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=False
#         )
#         payload = {param: value}
#         url = period_detail_url(period.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         period.refresh_from_db()
#         assert getattr(period, param) == payload[param]
#
#     @pytest.mark.parametrize(
#         'param, value', [('date_start', date(2023, 12, 31)), ('date_end', date(2024, 2, 1)), ('is_active', True)]
#     )
#     def test_error_on_period_partial_update(
#         self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass, param: str,
#         value: AbstractUser
#     ):
#         """Test error on partial update of a BudgetingPeriod."""
#         api_client.force_authenticate(base_user)
#         budgeting_period_factory(
#             user=base_user, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True
#         )
#         period = budgeting_period_factory(
#             user=base_user, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), is_active=False
#         )
#         old_value = getattr(period, param)
#         payload = {param: value}
#         url = period_detail_url(period.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         period.refresh_from_db()
#         assert getattr(period, param) == old_value
#
#     def test_period_full_update(
#         self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
#     ):
#         """Test successful full update of a BudgetingPeriod"""
#         api_client.force_authenticate(base_user)
#         payload_old = {
#             'name': '2023_06',
#             'date_start': date(2023, 6, 1),
#             'date_end': date(2023, 6, 30),
#             'is_active': False,
#         }
#         payload_new = {
#             'name': '2023_07',
#             'date_start': date(2023, 7, 1),
#             'date_end': date(2023, 7, 31),
#             'is_active': True,
#         }
#         period = budgeting_period_factory(user=base_user, **payload_old)
#         url = period_detail_url(period.id)
#
#         response = api_client.put(url, payload_new)
#
#         assert response.status_code == status.HTTP_200_OK
#         period.refresh_from_db()
#         for k, v in payload_new.items():
#             assert getattr(period, k) == v
#
#     @pytest.mark.parametrize(
#         'payload_new',
#         [
#             {'name': '2024_01', 'date_start': date(2024, 2, 1), 'date_end': date(2024, 2, 29), 'is_active': False},
#             {'name': '2024_02', 'date_start': date(2024, 1, 31), 'date_end': date(2024, 2, 29), 'is_active': False},
#             {'name': '2024_02', 'date_start': date(2024, 2, 1), 'date_end': date(2024, 2, 29), 'is_active': True},
#         ],
#     )
#     def test_error_on_period_full_update(
#         self, api_client: APIClient, base_user: AbstractUser,
#         budgeting_period_factory: FactoryMetaClass, payload_new: dict
#     ):
#         """Test error on full update of a BudgetingPeriod."""
#         api_client.force_authenticate(base_user)
#         budgeting_period_factory(
#             user=base_user, name='2024_01', date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True
#         )
#         payload_old = {
#             'name': '2024_02',
#             'date_start': date(2024, 2, 1),
#             'date_end': date(2024, 2, 29),
#             'is_active': False,
#         }
#
#         period = budgeting_period_factory(user=base_user, **payload_old)
#         url = period_detail_url(period.id)
#
#         response = api_client.patch(url, payload_new)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         period.refresh_from_db()
#         for k, v in payload_old.items():
#             assert getattr(period, k) == v
#
#     def test_delete_period(self, api_client: APIClient, base_user: AbstractUser,
#     budgeting_period_factory: FactoryMetaClass):
#         """Test deleting BudgetingPeriod."""
#         api_client.force_authenticate(base_user)
#         period = budgeting_period_factory(user=base_user)
#         url = period_detail_url(period.id)
#
#         assert BudgetingPeriod.objects.all().count() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not BudgetingPeriod.objects.all().exists()


@pytest.mark.django_db
class TestBudgetingPeriodApi:
    """Tests for BudgetingPeriodViewSet."""

    def test_auth_required(self, api_client: APIClient):
        """Test auth is required to call endpoint."""
        res = api_client.get(PERIODS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_periods_list(
        self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
    ):
        """Test retrieving list of periods."""
        api_client.force_authenticate(base_user)
        budgeting_period_factory(
            user=base_user, date_start=date(2023, 1, 1), date_end=date(2023, 1, 31), is_active=False
        )
        budgeting_period_factory(
            user=base_user, date_start=date(2023, 2, 1), date_end=date(2023, 2, 28), is_active=True
        )

        response = api_client.get(PERIODS_URL)

        periods = BudgetingPeriod.objects.all().order_by('-date_start')
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_periods_list_limited_to_user(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budgeting_period_factory: FactoryMetaClass
    ):
        """Test retrieved list of periods is limited to authenticated user."""
        user = user_factory()
        budgeting_period_factory(user=user)
        budgeting_period_factory()
        api_client.force_authenticate(user)

        response = api_client.get(PERIODS_URL)

        periods = BudgetingPeriod.objects.filter(user=user)
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_create_single_period(self, api_client: APIClient, base_user: AbstractUser):
        """Test creating single BudgetingPeriod."""
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date(2023, 1, 1), 'date_end': date(2023, 1, 31)}

        response = api_client.post(PERIODS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 1
        period = BudgetingPeriod.objects.get(id=response.data['id'])
        for key in payload:
            assert getattr(period, key) == payload[key]
        serializer = BudgetingPeriodSerializer(period)
        assert response.data == serializer.data

    def test_create_two_periods_by_one_user(self, api_client: APIClient, base_user: AbstractUser):
        """Test creating two valid BudgetingPeriods by single user."""
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

        response_1 = api_client.post(PERIODS_URL, payload_1)
        response_2 = api_client.post(PERIODS_URL, payload_2)

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 2
        for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
            period = BudgetingPeriod.objects.get(id=response.data['id'])
            for key in payload:
                assert getattr(period, key) == payload[key]

    def test_create_same_period_by_two_users(self, api_client: APIClient, user_factory: AbstractUser):
        """Test creating period with the same params by two users."""
        payload = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        user_1 = user_factory()
        api_client.force_authenticate(user_1)
        api_client.post(PERIODS_URL, payload)

        user_2 = user_factory()
        api_client.force_authenticate(user_2)
        api_client.post(PERIODS_URL, payload)

        assert BudgetingPeriod.objects.all().count() == 2
        assert BudgetingPeriod.objects.filter(user=user_1).count() == 1
        assert BudgetingPeriod.objects.filter(user=user_2).count() == 1

    def test_error_name_too_long(self, api_client: APIClient, base_user: AbstractUser):
        """Test error on creating BudgetingPeriod with name too long."""
        api_client.force_authenticate(base_user)
        max_length = BudgetingPeriod._meta.get_field('name').max_length
        payload = {
            'name': (max_length + 1) * 'a',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }

        response = api_client.post(PERIODS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not BudgetingPeriod.objects.filter(user=base_user).exists()

    def test_error_name_already_used(self, api_client: APIClient, base_user: AbstractUser):
        """Test error on creating BudgetingPeriod with already used name by the same user."""
        api_client.force_authenticate(base_user)
        payload = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 2),
        }
        BudgetingPeriod.objects.create(user=base_user, **payload)
        payload['date_start'] = date(2023, 1, 3)
        payload['date_end'] = date(2023, 1, 4)

        response = api_client.post(PERIODS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f"Users period with name {payload['name']} already exists."
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 1

    def test_create_active_period_successfully(self, api_client: APIClient, base_user: AbstractUser):
        """Test creating BudgetingPeriod with is_active=True successfully."""
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

        response_inactive = api_client.post(PERIODS_URL, payload_inactive)
        response_active = api_client.post(PERIODS_URL, payload_active)

        assert BudgetingPeriod.objects.all().count() == 2
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 2
        for response, payload in [(response_inactive, payload_inactive), (response_active, payload_active)]:
            assert response.status_code == status.HTTP_201_CREATED
            period = BudgetingPeriod.objects.get(id=response.data['id'])
            assert period.is_active == payload['is_active']

    def test_error_create_period_when_is_active_set_already(self, api_client: APIClient, base_user: AbstractUser):
        """Test error on creating new BudgetingPeriod with is_active=True, when another user's period active already."""
        api_client.force_authenticate(base_user)
        payload_1 = {
            'name': '2023_01',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }
        active_period = BudgetingPeriod.objects.create(user=base_user, **payload_1)
        payload_2 = {
            'name': '2023_02',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }

        response = api_client.post(PERIODS_URL, payload_2)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'is_active' in response.data
        assert response.data['is_active'][0] == 'User already has active budgeting period.'
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 1
        assert BudgetingPeriod.objects.filter(user=base_user).first() == active_period

    def test_is_active_default_value(self, api_client: APIClient, base_user: AbstractUser):
        """Test creating BudgetingPeriod without passing is_active ends with default False value."""
        api_client.force_authenticate(base_user)
        payload = {
            'name': '2023_02',
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': '',
        }

        response = api_client.post(PERIODS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert BudgetingPeriod.objects.all().count() == 1
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 1
        assert response.data['is_active'] is False

    @pytest.mark.parametrize('date_start, date_end', (('', date.today()), (date.today(), ''), ('', '')))
    def test_error_date_blank(
        self, api_client: APIClient, base_user: AbstractUser, date_start: Optional[date], date_end: Optional[date]
    ):
        """Test error on creating BudgetingPeriod with date_start or date_end blank."""
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date_start, 'date_end': date_end, 'is_active': False}
        error_message = 'Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'

        response = api_client.post(PERIODS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'date_start' in response.data or 'date_end' in response.data
        assert (
            response.data.get('date_start', [''])[0] == error_message
            or response.data.get('date_end', [''])[0] == error_message
        )
        assert not BudgetingPeriod.objects.filter(user=base_user).exists()

    def test_error_date_end_before_date_start(self, api_client: APIClient, base_user: AbstractUser):
        """Test error on creating BudgetingPeriod with date_end earlier than date_start."""
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date(2023, 5, 1), 'date_end': date(2023, 4, 30), 'is_active': False}

        response = api_client.post(PERIODS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert response.data['non_field_errors'][0] == 'Start date should be earlier than end date.'
        assert not BudgetingPeriod.objects.filter(user=base_user).exists()

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
    def test_error_date_invalid(self, api_client: APIClient, base_user: AbstractUser, date_start: date, date_end: date):
        """Test error on creating BudgetingPeriod with invalid dates."""
        api_client.force_authenticate(base_user)
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
        BudgetingPeriod.objects.create(user=base_user, **payload_1)
        BudgetingPeriod.objects.create(user=base_user, **payload_2)

        response = api_client.post(PERIODS_URL, payload_invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert (
            response.data['non_field_errors'][0]
            == "Budgeting period date range collides with other user's budgeting periods."
        )
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 2

    def test_get_period_details(
        self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
    ):
        """Test get BudgetingPeriod details."""
        api_client.force_authenticate(base_user)
        period = budgeting_period_factory(user=base_user)
        url = period_detail_url(period.id)

        response = api_client.get(url)
        serializer = BudgetingPeriodSerializer(period)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_period_details_unauthenticated(
        self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
    ):
        """Test error on getting BudgetingPeriod details being unauthenticated."""
        period = budgeting_period_factory(user=base_user)
        url = period_detail_url(period.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_other_user_period_details(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budgeting_period_factory: FactoryMetaClass
    ):
        """Test error on getting other user's BudgetingPeriod details."""
        user_1 = user_factory()
        user_2 = user_factory()
        period = budgeting_period_factory(user=user_1)
        api_client.force_authenticate(user_2)

        url = period_detail_url(period.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'param, value', [('date_start', date(2024, 1, 2)), ('date_end', date(2024, 1, 30)), ('is_active', True)]
    )
    def test_period_partial_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budgeting_period_factory: FactoryMetaClass,
        param: str,
        value: AbstractUser,
    ):
        """Test partial update of a BudgetingPeriod"""
        api_client.force_authenticate(base_user)
        period = budgeting_period_factory(
            user=base_user, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=False
        )
        payload = {param: value}
        url = period_detail_url(period.id)

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
        budgeting_period_factory: FactoryMetaClass,
        param: str,
        value: AbstractUser,
    ):
        """Test error on partial update of a BudgetingPeriod."""
        api_client.force_authenticate(base_user)
        budgeting_period_factory(
            user=base_user, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True
        )
        period = budgeting_period_factory(
            user=base_user, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), is_active=False
        )
        old_value = getattr(period, param)
        payload = {param: value}
        url = period_detail_url(period.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        assert getattr(period, param) == old_value

    def test_period_full_update(
        self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
    ):
        """Test successful full update of a BudgetingPeriod"""
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
        period = budgeting_period_factory(user=base_user, **payload_old)
        url = period_detail_url(period.id)

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
        budgeting_period_factory: FactoryMetaClass,
        payload_new: dict,
    ):
        """Test error on full update of a BudgetingPeriod."""
        api_client.force_authenticate(base_user)
        budgeting_period_factory(
            user=base_user, name='2024_01', date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True
        )
        payload_old = {
            'name': '2024_02',
            'date_start': date(2024, 2, 1),
            'date_end': date(2024, 2, 29),
            'is_active': False,
        }

        period = budgeting_period_factory(user=base_user, **payload_old)
        url = period_detail_url(period.id)

        response = api_client.patch(url, payload_new)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        period.refresh_from_db()
        for k, v in payload_old.items():
            assert getattr(period, k) == v

    def test_delete_period(
        self, api_client: APIClient, base_user: AbstractUser, budgeting_period_factory: FactoryMetaClass
    ):
        """Test deleting BudgetingPeriod."""
        api_client.force_authenticate(base_user)
        period = budgeting_period_factory(user=base_user)
        url = period_detail_url(period.id)

        assert BudgetingPeriod.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BudgetingPeriod.objects.all().exists()
