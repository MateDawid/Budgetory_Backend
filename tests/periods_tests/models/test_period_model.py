from datetime import date

import pytest
from django.db import DataError, IntegrityError

from periods.models.choices.period_status import PeriodStatus
from periods.models.period_model import Period
from wallets.models.wallet_model import Wallet


@pytest.mark.django_db
class TestPeriodModel:
    """Tests for Period model"""

    def test_create_first_period_successful(self, wallet: Wallet):
        """
        GIVEN: Wallet model instance in database.
        WHEN: Period instance create attempt with valid data.
        THEN: Period model instance exists in database with given data.
        """
        payload = {
            "name": "2023_01",
            "wallet": wallet,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }

        period = Period.objects.create(**payload)

        for k, v in payload.items():
            assert getattr(period, k) == v
        assert Period.objects.filter(wallet=wallet).count() == 1
        assert str(period) == f"{period.name} ({period.wallet.name})"
        assert period.previous_period is None

    def test_previous_period_assign(self, wallet: Wallet):
        """
        GIVEN: Three Period model instances for Wallet in database
        WHEN: Period instance create attempt with valid data.
        THEN: Latest of existing Periods saved as previous_period for created one..
        """
        Period.objects.bulk_create(
            [
                Period(
                    name="2023_01",
                    wallet=wallet,
                    status=PeriodStatus.CLOSED,
                    date_start=date(2023, 1, 1),
                    date_end=date(2023, 1, 31),
                ),
                Period(
                    name="2023_02",
                    wallet=wallet,
                    status=PeriodStatus.CLOSED,
                    date_start=date(2023, 2, 1),
                    date_end=date(2023, 2, 28),
                ),
            ]
        )
        latest_period = Period.objects.create(
            name="2023_03",
            wallet=wallet,
            status=PeriodStatus.CLOSED,
            date_start=date(2023, 3, 1),
            date_end=date(2023, 3, 31),
        )

        new_period = Period.objects.create(
            name="2023_04",
            wallet=wallet,
            status=PeriodStatus.DRAFT,
            date_start=date(2023, 4, 1),
            date_end=date(2023, 4, 30),
        )

        assert new_period.previous_period == latest_period

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, wallet: Wallet):
        """
        GIVEN: Wallet model instance in database.
        WHEN: Period instance create attempt with name too long in payload.
        THEN: DataError raised, object not created in database.
        """
        max_length = Period._meta.get_field("name").max_length
        payload = {
            "name": (max_length + 1) * "a",
            "wallet": wallet,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }

        with pytest.raises(DataError) as exc:
            Period.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Period.objects.filter(wallet=wallet).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, wallet: Wallet):
        """
        GIVEN: Single Period for Wallet in database.
        WHEN: Period instance create attempt with name already used for existing Period.
        THEN: DataError raised, object not created in database.
        """
        payload = {
            "name": "2023_01",
            "wallet": wallet,
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        Period.objects.create(**payload)

        payload["date_start"] = date(2023, 2, 1)
        payload["date_end"] = date(2023, 2, 28)
        with pytest.raises(IntegrityError) as exc:
            Period.objects.create(**payload)
        assert f'DETAIL:  Key (name, wallet_id)=({payload["name"]}, {wallet.id}) already exists.' in str(exc.value)
        assert Period.objects.filter(wallet=wallet).count() == 1

    def test_create_active_period_successfully(self, wallet: Wallet):
        """
        GIVEN: Single closed Period for Wallet in database.
        WHEN: Period instance create attempt with stats = PeriodStatus.ACTIVE.
        THEN: Two Period model instances existing in database - one active, one closed.
        """
        payload_inactive = {
            "name": "2023_01",
            "wallet": wallet,
            "status": PeriodStatus.CLOSED,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        payload_active = {
            "name": "2023_02",
            "wallet": wallet,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 2, 1),
            "date_end": date(2023, 2, 28),
        }

        period_inactive = Period.objects.create(**payload_inactive)
        period_active = Period.objects.create(**payload_active)
        assert period_inactive.status is PeriodStatus.CLOSED
        assert period_active.status is PeriodStatus.ACTIVE
        assert Period.objects.filter(wallet=wallet).count() == 2
