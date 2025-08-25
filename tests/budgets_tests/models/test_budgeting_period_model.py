from datetime import date

import pytest
from django.db import DataError, IntegrityError

from budgets.models.budget_model import Budget
from budgets.models.budgeting_period_model import BudgetingPeriod
from budgets.models.choices.period_status import PeriodStatus


@pytest.mark.django_db
class TestBudgetingPeriodModel:
    """Tests for BudgetingPeriod model"""

    def test_create_first_period_successful(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: BudgetingPeriod instance create attempt with valid data.
        THEN: BudgetingPeriod model instance exists in database with given data.
        """
        payload = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }

        period = BudgetingPeriod.objects.create(**payload)

        for k, v in payload.items():
            assert getattr(period, k) == v
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1
        assert str(period) == f"{period.name} ({period.budget.name})"
        assert period.previous_period is None

    def test_previous_period_assign(self, budget: Budget):
        """
        GIVEN: Three BudgetingPeriod model instances for Budget in database
        WHEN: BudgetingPeriod instance create attempt with valid data.
        THEN: Latest of existing BudgetingPeriods saved as previous_period for created one..
        """
        BudgetingPeriod.objects.bulk_create(
            [
                BudgetingPeriod(
                    name="2023_01",
                    budget=budget,
                    status=PeriodStatus.CLOSED,
                    date_start=date(2023, 1, 1),
                    date_end=date(2023, 1, 31),
                ),
                BudgetingPeriod(
                    name="2023_02",
                    budget=budget,
                    status=PeriodStatus.CLOSED,
                    date_start=date(2023, 2, 1),
                    date_end=date(2023, 2, 28),
                ),
            ]
        )
        latest_period = BudgetingPeriod.objects.create(
            name="2023_03",
            budget=budget,
            status=PeriodStatus.CLOSED,
            date_start=date(2023, 3, 1),
            date_end=date(2023, 3, 31),
        )

        new_period = BudgetingPeriod.objects.create(
            name="2023_04",
            budget=budget,
            status=PeriodStatus.DRAFT,
            date_start=date(2023, 4, 1),
            date_end=date(2023, 4, 30),
        )

        assert new_period.previous_period == latest_period

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: BudgetingPeriod instance create attempt with name too long in payload.
        THEN: DataError raised, object not created in database.
        """
        max_length = BudgetingPeriod._meta.get_field("name").max_length
        payload = {
            "name": (max_length + 1) * "a",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }

        with pytest.raises(DataError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not BudgetingPeriod.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, budget: Budget):
        """
        GIVEN: Single BudgetingPeriod for Budget in database.
        WHEN: BudgetingPeriod instance create attempt with name already used for existing BudgetingPeriod.
        THEN: DataError raised, object not created in database.
        """
        payload = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        BudgetingPeriod.objects.create(**payload)

        payload["date_start"] = date(2023, 2, 1)
        payload["date_end"] = date(2023, 2, 28)
        with pytest.raises(IntegrityError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert f'DETAIL:  Key (name, budget_id)=({payload["name"]}, {budget.id}) already exists.' in str(exc.value)
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1

    def test_create_active_period_successfully(self, budget: Budget):
        """
        GIVEN: Single closed BudgetingPeriod for Budget in database.
        WHEN: BudgetingPeriod instance create attempt with stats = PeriodStatus.ACTIVE.
        THEN: Two BudgetingPeriod model instances existing in database - one active, one closed.
        """
        payload_inactive = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.CLOSED,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        payload_active = {
            "name": "2023_02",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 2, 1),
            "date_end": date(2023, 2, 28),
        }

        period_inactive = BudgetingPeriod.objects.create(**payload_inactive)
        period_active = BudgetingPeriod.objects.create(**payload_active)
        assert period_inactive.status is PeriodStatus.CLOSED
        assert period_active.status is PeriodStatus.ACTIVE
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 2
