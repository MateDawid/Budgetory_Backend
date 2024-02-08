from typing import Any

import pytest
from deposits.models import Deposit
from deposits.serializers import DepositSerializer
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

DEPOSITS_URL = reverse('deposits:deposit-list')


def deposit_detail_url(deposit_id):
    """Create and return a deposit detail URL."""
    return reverse('deposits:deposit-detail', args=[deposit_id])


@pytest.mark.django_db
class TestDepositApi:
    """Tests for DepositViewSet."""

    def test_auth_required(self, api_client: APIClient):
        """Test auth is required to call endpoint."""
        res = api_client.get(DEPOSITS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_deposits_list(self, api_client: APIClient, base_user: Any, deposit_factory: FactoryMetaClass):
        """Test retrieving list of deposits."""
        api_client.force_authenticate(base_user)
        deposit_factory(user=base_user)
        deposit_factory(user=base_user)

        response = api_client.get(DEPOSITS_URL)

        deposits = Deposit.objects.all()
        serializer = DepositSerializer(deposits, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_deposits_list_limited_to_user(
        self, api_client: APIClient, user_factory: FactoryMetaClass, deposit_factory: FactoryMetaClass
    ):
        """Test retrieved list of deposits is limited to authenticated user."""
        user = user_factory()
        deposit_factory(user=user)
        deposit_factory()
        api_client.force_authenticate(user)

        response = api_client.get(DEPOSITS_URL)

        periods = Deposit.objects.filter(user=user)
        serializer = DepositSerializer(periods, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_create_single_deposit(self, api_client: APIClient, base_user: Any):
        """Test creating single Deposit."""
        api_client.force_authenticate(base_user)
        payload = {'name': 'My account', 'description': 'Account that I use.', 'is_active': True}

        response = api_client.post(DEPOSITS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.filter(user=base_user).count() == 1
        deposit = Deposit.objects.get(id=response.data['id'])
        for key in payload:
            assert getattr(deposit, key) == payload[key]
        serializer = DepositSerializer(deposit)
        assert response.data == serializer.data

    def test_create_two_deposits_by_one_user(self, api_client: APIClient, base_user: Any):
        """Test creating two valid Deposits by single user."""
        api_client.force_authenticate(base_user)
        payload_1 = {'name': 'My account', 'description': 'Account that I use.', 'is_active': True}
        payload_2 = {'name': 'Old account', 'description': 'Not used account.', 'is_active': False}

        response_1 = api_client.post(DEPOSITS_URL, payload_1)
        response_2 = api_client.post(DEPOSITS_URL, payload_2)

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.filter(user=base_user).count() == 2
        for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
            period = Deposit.objects.get(id=response.data['id'])
            for key in payload:
                assert getattr(period, key) == payload[key]

    def test_create_same_deposit_by_two_users(self, api_client: APIClient, user_factory: Any):
        """Test creating deposit with the same params by two users."""
        payload = {'name': 'My account', 'description': 'Account that I use.', 'is_active': True}
        user_1 = user_factory()
        api_client.force_authenticate(user_1)
        api_client.post(DEPOSITS_URL, payload)

        user_2 = user_factory()
        api_client.force_authenticate(user_2)
        api_client.post(DEPOSITS_URL, payload)

        assert Deposit.objects.all().count() == 2
        assert Deposit.objects.filter(user=user_1).count() == 1
        assert Deposit.objects.filter(user=user_2).count() == 1

    def test_error_name_too_long(self, api_client: APIClient, base_user: Any):
        """Test error on creating Deposit with name too long."""
        api_client.force_authenticate(base_user)
        max_length = Deposit._meta.get_field('name').max_length
        payload = {'name': (max_length + 1) * 'a', 'description': 'Account that I use.', 'is_active': True}

        response = api_client.post(DEPOSITS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not Deposit.objects.filter(user=base_user).exists()

    def test_error_name_already_used(self, api_client: APIClient, base_user: Any):
        """Test error on creating Deposit with already used name by the same user."""
        api_client.force_authenticate(base_user)
        payload = {'name': 'My account', 'description': 'Account that I use.', 'is_active': True}
        Deposit.objects.create(user=base_user, **payload)

        response = api_client.post(DEPOSITS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f"Users deposit with name {payload['name']} already exists."
        assert Deposit.objects.filter(user=base_user).count() == 1

    def test_error_description_too_long(self, api_client: APIClient, base_user: Any):
        """Test error on creating Deposit with description too long."""
        api_client.force_authenticate(base_user)
        max_length = Deposit._meta.get_field('description').max_length
        payload = {'name': 'My account', 'description': (max_length + 1) * 'a', 'is_active': True}

        response = api_client.post(DEPOSITS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not Deposit.objects.filter(user=base_user).exists()

    def test_is_active_default_value(self, api_client: APIClient, base_user: Any):
        """Test creating Deposit without passing is_active ends with default value."""
        api_client.force_authenticate(base_user)
        default = Deposit._meta.get_field('is_active').default
        payload = {'name': 'My account', 'description': 'Account that I use.'}

        response = api_client.post(DEPOSITS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.all().count() == 1
        assert Deposit.objects.filter(user=base_user).count() == 1
        assert response.data['is_active'] == default

    # def test_get_period_details(
    #     self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass
    # ):
    #     """Test get BudgetingPeriod details."""
    #     api_client.force_authenticate(base_user)
    #     period = budgeting_period_factory(user=base_user)
    #     url = period_detail_url(period.id)
    #
    #     response = api_client.get(url)
    #     serializer = BudgetingPeriodSerializer(period)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     assert response.data == serializer.data
    #
    # def test_error_get_period_details_unauthenticated(
    #     self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass
    # ):
    #     """Test error on getting BudgetingPeriod details being unauthenticated."""
    #     period = budgeting_period_factory(user=base_user)
    #     url = period_detail_url(period.id)
    #
    #     response = api_client.get(url)
    #
    #     assert response.status_code == status.HTTP_401_UNAUTHORIZED
    #
    # def test_error_get_other_user_period_details(
    #     self, api_client: APIClient, user_factory: FactoryMetaClass, budgeting_period_factory: FactoryMetaClass
    # ):
    #     """Test error on getting other user's BudgetingPeriod details."""
    #     user_1 = user_factory()
    #     user_2 = user_factory()
    #     period = budgeting_period_factory(user=user_1)
    #     api_client.force_authenticate(user_2)
    #
    #     url = period_detail_url(period.id)
    #     response = api_client.get(url)
    #
    #     assert response.status_code == status.HTTP_404_NOT_FOUND
    #
    # @pytest.mark.parametrize(
    #     'param, value', [('date_start', date(2024, 1, 2)), ('date_end', date(2024, 1, 30)), ('is_active', True)]
    # )
    # def test_period_partial_update(
    #     self, api_client: APIClient, base_user: Any,
    #     budgeting_period_factory: FactoryMetaClass, param: str, value: Any
    # ):
    #     """Test partial update of a BudgetingPeriod"""
    #     api_client.force_authenticate(base_user)
    #     period = budgeting_period_factory(
    #         user=base_user, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=False
    #     )
    #     payload = {param: value}
    #     url = period_detail_url(period.id)
    #
    #     response = api_client.patch(url, payload)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     period.refresh_from_db()
    #     assert getattr(period, param) == payload[param]
    #
    # @pytest.mark.parametrize(
    #     'param, value', [('date_start', date(2023, 12, 31)), ('date_end', date(2024, 2, 1)), ('is_active', True)]
    # )
    # def test_error_on_period_partial_update(
    #     self, api_client: APIClient, base_user: Any,
    #     budgeting_period_factory: FactoryMetaClass, param: str, value: Any
    # ):
    #     """Test error on partial update of a BudgetingPeriod."""
    #     api_client.force_authenticate(base_user)
    #     budgeting_period_factory(
    #         user=base_user, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True
    #     )
    #     period = budgeting_period_factory(
    #         user=base_user, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), is_active=False
    #     )
    #     old_value = getattr(period, param)
    #     payload = {param: value}
    #     url = period_detail_url(period.id)
    #
    #     response = api_client.patch(url, payload)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     period.refresh_from_db()
    #     assert getattr(period, param) == old_value
    #
    # def test_period_full_update(
    #     self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass
    # ):
    #     """Test successful full update of a BudgetingPeriod"""
    #     api_client.force_authenticate(base_user)
    #     payload_old = {
    #         'name': '2023_06',
    #         'date_start': date(2023, 6, 1),
    #         'date_end': date(2023, 6, 30),
    #         'is_active': False,
    #     }
    #     payload_new = {
    #         'name': '2023_07',
    #         'date_start': date(2023, 7, 1),
    #         'date_end': date(2023, 7, 31),
    #         'is_active': True,
    #     }
    #     period = budgeting_period_factory(user=base_user, **payload_old)
    #     url = period_detail_url(period.id)
    #
    #     response = api_client.put(url, payload_new)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     period.refresh_from_db()
    #     for k, v in payload_new.items():
    #         assert getattr(period, k) == v
    #
    # @pytest.mark.parametrize(
    #     'payload_new',
    #     [
    #         {'name': '2024_01', 'date_start': date(2024, 2, 1), 'date_end': date(2024, 2, 29), 'is_active': False},
    #         {'name': '2024_02', 'date_start': date(2024, 1, 31), 'date_end': date(2024, 2, 29), 'is_active': False},
    #         {'name': '2024_02', 'date_start': date(2024, 2, 1), 'date_end': date(2024, 2, 29), 'is_active': True},
    #     ],
    # )
    # def test_error_on_period_full_update(
    #     self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass, payload_new: dict
    # ):
    #     """Test error on full update of a BudgetingPeriod."""
    #     api_client.force_authenticate(base_user)
    #     budgeting_period_factory(
    #         user=base_user, name='2024_01', date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=True
    #     )
    #     payload_old = {
    #         'name': '2024_02',
    #         'date_start': date(2024, 2, 1),
    #         'date_end': date(2024, 2, 29),
    #         'is_active': False,
    #     }
    #
    #     period = budgeting_period_factory(user=base_user, **payload_old)
    #     url = period_detail_url(period.id)
    #
    #     response = api_client.patch(url, payload_new)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     period.refresh_from_db()
    #     for k, v in payload_old.items():
    #         assert getattr(period, k) == v
    #
    # def test_delete_period(self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass):
    #     """Test deleting BudgetingPeriod."""
    #     api_client.force_authenticate(base_user)
    #     period = budgeting_period_factory(user=base_user)
    #     url = period_detail_url(period.id)
    #
    #     assert BudgetingPeriod.objects.all().count() == 1
    #
    #     response = api_client.delete(url)
    #
    #     assert response.status_code == status.HTTP_204_NO_CONTENT
    #     assert not BudgetingPeriod.objects.all().exists()
