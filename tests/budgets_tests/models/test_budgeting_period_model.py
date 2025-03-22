from datetime import date

import pytest
from django.core.exceptions import ValidationError
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

    def test_create_two_periods_successful(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: Two BudgetingPeriod instances create attempt with valid, not colliding data.
        THEN: Two BudgetingPeriod instances existing in database.
        """
        payload_1 = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        payload_2 = {
            "name": "2023_02",
            "budget": budget,
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 2, 1),
            "date_end": date(2023, 2, 28),
        }
        budgeting_period_1 = BudgetingPeriod.objects.create(**payload_1)
        budgeting_period_2 = BudgetingPeriod.objects.create(**payload_2)
        for budgeting_period, payload in [(budgeting_period_1, payload_1), (budgeting_period_2, payload_2)]:
            for k, v in payload.items():
                assert getattr(budgeting_period, k) == v
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 2

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

    def test_error_active_period_already_exists(self, budget: Budget):
        """
        GIVEN: Single active BudgetingPeriod for Budget in database.
        WHEN: BudgetingPeriod instance create attempt with status = PeriodStatus.ACTIVE.
        THEN: ValidationError raised as active period already exists. New period not created in database.
        """
        payload_1 = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        active_period = BudgetingPeriod.objects.create(**payload_1)

        payload_2 = {
            "name": "2023_02",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        with pytest.raises(ValidationError) as exc:
            BudgetingPeriod.objects.create(**payload_2)
        assert exc.value.message == "status: Active period already exists in Budget."
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 1
        assert BudgetingPeriod.objects.filter(budget=budget).first() == active_period

    def test_error_closed_period_cannot_be_changed(self, budget: Budget):
        """
        GIVEN: Single closed BudgetingPeriod for Budget in database.
        WHEN: BudgetingPeriod instance update attempt.
        THEN: ValidationError raised as closed period cannot be changed. Period not updated in database.
        """
        payload_1 = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.CLOSED,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        period = BudgetingPeriod.objects.create(**payload_1)
        with pytest.raises(ValidationError) as exc:
            period.name = "2023_01_1"
            period.save()
        period.refresh_from_db()
        assert exc.value.message == "status: Closed period cannot be changed."
        assert period.name == payload_1["name"]

    def test_error_active_period_cannot_be_draft_again(self, budget: Budget):
        """
        GIVEN: Single active BudgetingPeriod for Budget in database.
        WHEN: BudgetingPeriod instance update attempt with draft status.
        THEN: ValidationError raised as active period cannot be moved back to draft status.
        Period not updated in database.
        """
        payload_1 = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 1, 1),
            "date_end": date(2023, 1, 31),
        }
        period = BudgetingPeriod.objects.create(**payload_1)
        with pytest.raises(ValidationError) as exc:
            period.status = PeriodStatus.DRAFT
            period.save()
        period.refresh_from_db()
        assert exc.value.message == "status: Active period cannot be moved back to Draft status."
        assert period.status == payload_1["status"]

    def test_error_date_end_before_date_start(self, budget: Budget):
        """
        GIVEN: Single Budget in database.
        WHEN: BudgetingPeriod instance create attempt with date_end before date_start.
        THEN: ValidationError raised. New period not created in database.
        """
        payload = {
            "name": "2023_01",
            "budget": budget,
            "status": PeriodStatus.ACTIVE,
            "date_start": date(2023, 5, 1),
            "date_end": date(2023, 4, 30),
        }

        with pytest.raises(ValidationError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert exc.value.code == "date-invalid"
        assert exc.value.message == "start_date: Start date should be earlier than end date."
        assert not BudgetingPeriod.objects.filter(budget=budget).exists()

    @pytest.mark.parametrize(
        "date_start, date_end",
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
    def test_error_date_invalid(self, budget: Budget, date_start: date, date_end: date):
        """
        GIVEN: Two BudgetingPeriods for single Budget in database created.
        WHEN: BudgetingPeriod instance create attempt with date_start and/or date_end colliding with
        existing BudgetingPeriods.
        THEN: ValidationError raised. New period not created in database.
        """
        payload_1 = {
            "name": "2023_06",
            "budget": budget,
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 6, 1),
            "date_end": date(2023, 6, 30),
        }
        payload_2 = {
            "name": "2023_07",
            "budget": budget,
            "status": PeriodStatus.DRAFT,
            "date_start": date(2023, 7, 1),
            "date_end": date(2023, 7, 31),
        }
        payload_invalid = {
            "name": "invalid",
            "budget": budget,
            "status": PeriodStatus.DRAFT,
            "date_start": date_start,
            "date_end": date_end,
        }
        BudgetingPeriod.objects.create(**payload_1)
        BudgetingPeriod.objects.create(**payload_2)
        with pytest.raises(ValidationError) as exc:
            BudgetingPeriod.objects.create(**payload_invalid)
        assert exc.value.code == "period-range-invalid"
        assert exc.value.message == "date_start: Period date range collides with other period in Budget."
        assert BudgetingPeriod.objects.filter(budget=budget).count() == 2
