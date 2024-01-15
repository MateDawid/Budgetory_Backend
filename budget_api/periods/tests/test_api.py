from datetime import date
from typing import Any, Optional

import pytest
from django.urls import reverse
from factory.base import FactoryMetaClass
from periods.models import BudgetingPeriod
from periods.serializers import BudgetingPeriodSerializer
from rest_framework import status
from rest_framework.test import APIClient

PERIODS_URL = reverse('periods:budgetingperiod-list')


def period_detail_url(period_id):
    """Create and return a budgeting period detail URL."""
    return reverse('periods:budgetingperiod-detail', args=[period_id])


@pytest.mark.django_db
class TestBudgetingPeriodApi:
    """Tests for BudgetingPeriodViewSet."""

    def test_auth_required(self, api_client: APIClient):
        """Test auth is required to call endpoint."""
        res = api_client.get(PERIODS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_periods_list(
        self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass
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

    def test_create_single_period(self, api_client: APIClient, base_user: Any):
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

    def test_create_two_periods_by_one_user(self, api_client: APIClient, base_user: Any):
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

    def test_create_same_period_by_two_users(self, api_client: APIClient, user_factory: Any):
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

    def test_error_name_too_long(self, api_client: APIClient, base_user: Any):
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

    def test_error_name_already_used(self, api_client: APIClient, base_user: Any):
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

    def test_create_active_period_successfully(self, api_client: APIClient, base_user: Any):
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

    def test_error_create_period_when_is_active_set_already(self, api_client: APIClient, base_user: Any):
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

    def test_is_active_default_value(self, api_client: APIClient, base_user: Any):
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
        self, api_client: APIClient, base_user: Any, date_start: Optional[date], date_end: Optional[date]
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

    def test_error_date_end_before_date_start(self, api_client: APIClient, base_user: Any):
        """Test error on creating BudgetingPeriod with date_end earlier than date_start."""
        api_client.force_authenticate(base_user)
        payload = {'name': '2023_01', 'date_start': date(2023, 5, 1), 'date_end': date(2023, 4, 30), 'is_active': False}

        response = api_client.post(PERIODS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'date_start' in response.data
        assert response.data['date_start'][0] == 'Start date should be earlier than end date.'
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
    def test_error_date_invalid(self, api_client: APIClient, base_user: Any, date_start: date, date_end: date):
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
        assert 'date_start' in response.data
        assert (
            response.data['date_start'][0]
            == "Budgeting period date range collides with other user's budgeting periods."
        )
        assert BudgetingPeriod.objects.filter(user=base_user).count() == 2

    def test_get_period_details(
        self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass
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
        self, api_client: APIClient, base_user: Any, budgeting_period_factory: FactoryMetaClass
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

    # @pytest.mark.parametrize('param, value', [('version', '1.1.2'), ('is_latest', True)])
    # def test_tutorial_version_partial_update(
    #     self,
    #     api_client: APIClient,
    #     tutorial: Tutorial,
    #     tutorial_version_factory: FactoryMetaClass,
    #     param: str,
    #     value: Any,
    # ):
    #     """Test partial update of a TutorialVersion"""
    #     version = tutorial_version_factory(version='1.1.1', tutorial=tutorial, is_latest=False)
    #     payload = {param: value}
    #
    #     url = tutorial_version_detail_url(tutorial.id, version.id)
    #     response = api_client.patch(url, payload)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     version.refresh_from_db()
    #     assert getattr(version, param) == payload[param]
    #
    # @pytest.mark.parametrize('param, value', [('version', '1.1.1'), ('is_latest', True)])
    # def test_error_on_tutorial_version_partial_update(
    #     self,
    #     api_client: APIClient,
    #     tutorial: Tutorial,
    #     tutorial_version_factory: FactoryMetaClass,
    #     param: str,
    #     value: Any,
    # ):
    #     """Test error on partial update of a TutorialVersion."""
    #     tutorial_version_factory(version='1.1.1', tutorial=tutorial, is_latest=True)
    #     version = tutorial_version_factory(version='1.1.2', tutorial=tutorial, is_latest=False)
    #     old_value = getattr(version, param)
    #     payload = {param: value}
    #     url = tutorial_version_detail_url(tutorial.id, version.id)
    #
    #     response = api_client.patch(url, payload)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     version.refresh_from_db()
    #     assert getattr(version, param) == old_value
    #
    # def test_tutorial_version_full_update(
    #     self, api_client: APIClient, tutorial: Tutorial, tutorial_version_factory: FactoryMetaClass
    # ):
    #     """Test successful full update of a TutorialVersion"""
    #     payload_old = {'version': '1.1.1', 'is_latest': False}
    #     payload_new = {'version': '1.1.2', 'is_latest': True}
    #     version = tutorial_version_factory(**payload_old)
    #     url = tutorial_version_detail_url(tutorial.id, version.id)
    #
    #     response = api_client.put(url, payload_new)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     version.refresh_from_db()
    #     for k, v in payload_new.items():
    #         assert getattr(version, k) == v
    #
    # @pytest.mark.parametrize(
    #     'payload_new',
    #     [
    #         {'version': '1.1.1', 'is_latest': False},
    #         {'version': '1.1.2', 'is_latest': True},
    #         {'version': '1.1.1', 'is_latest': True},
    #     ],
    # )
    # def test_error_on_tutorial_version_full_update(
    #     self, api_client: APIClient, tutorial: Tutorial, tutorial_version_factory: FactoryMetaClass, payload_new: dict
    # ):
    #     """Test error on partial update of a TutorialVersion."""
    #     tutorial_version_factory(version='1.1.1', tutorial=tutorial, is_latest=True)
    #     payload_old = {'version': '1.1.2', 'is_latest': False}
    #     version = tutorial_version_factory(tutorial=tutorial, **payload_old)
    #     url = tutorial_version_detail_url(tutorial.id, version.id)
    #
    #     response = api_client.patch(url, payload_new)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     version.refresh_from_db()
    #     for k, v in payload_old.items():
    #         assert getattr(version, k) == v
    #
    # def test_delete_tutorial_version(self, api_client: APIClient, tutorial_version_factory: FactoryMetaClass):
    #     """Test deleting TutorialVersion."""
    #     version = tutorial_version_factory()
    #     url = tutorial_version_detail_url(version.tutorial.id, version.id)
    #
    #     assert TutorialVersion.objects.all().count() == 1
    #
    #     response = api_client.delete(url)
    #
    #     assert response.status_code == status.HTTP_204_NO_CONTENT
    #     assert not TutorialVersion.objects.all().exists()
