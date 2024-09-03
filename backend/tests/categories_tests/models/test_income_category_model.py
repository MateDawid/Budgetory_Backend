import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError

from budgets.models import Budget
from categories.models.income_category_model import IncomeCategory
from categories.models.transfer_category_choices import CategoryType, IncomeCategoryPriority


@pytest.mark.django_db
class TestIncomeCategoryModel:
    """Tests for IncomeCategory proxy model"""

    PAYLOAD = {
        "name": "Salary",
        "description": "Category for salary.",
        "is_active": True,
        "priority": IncomeCategoryPriority.REGULAR,
    }

    def test_save_income_category(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategory instance save attempt with valid data.
        THEN: IncomeCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()

        income_category = IncomeCategory(budget=budget, **payload)
        income_category.full_clean()
        income_category.save()
        income_category.refresh_from_db()

        for key in payload:
            assert getattr(income_category, key) == payload[key]
        assert IncomeCategory.objects.filter(budget=budget).count() == 1
        assert income_category.category_type == CategoryType.INCOME
        assert str(income_category) == f"({income_category.category_type.label}) {income_category.name}"

    def test_create_income_category(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategory instance create attempt with valid data.
        THEN: IncomeCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()

        income_category = IncomeCategory.objects.create(budget=budget, **payload)

        for key in payload:
            assert getattr(income_category, key) == payload[key]
        assert IncomeCategory.objects.filter(budget=budget).count() == 1
        assert income_category.category_type == CategoryType.INCOME
        assert str(income_category) == f"({income_category.category_type.label}) {income_category.name}"

    def test_proper_category_type_on_income_category_save(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategory instance save attempt with category_type=CategoryType.EXPENSE in payload.
        THEN: IncomeCategory model instance exists in database with category_type=CategoryType.INCOME.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = CategoryType.EXPENSE.value

        income_category = IncomeCategory(budget=budget, **payload)
        income_category.full_clean()
        income_category.save()

        assert IncomeCategory.objects.filter(budget=budget).count() == 1
        assert income_category.category_type == CategoryType.INCOME

    def test_proper_category_type_on_income_category_create(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategory instance create attempt with category_type=CategoryType.EXPENSE in payload.
        THEN: IncomeCategory model instance exists in database category_type=CategoryType.INCOME.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = CategoryType.EXPENSE.value

        income_category = IncomeCategory.objects.create(budget=budget, **payload)

        assert IncomeCategory.objects.filter(budget=budget).count() == 1
        assert income_category.category_type == CategoryType.INCOME

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(self, budget: Budget, field_name: str):
        """
        GIVEN: Budget model instances in database.
        WHEN: IncomeCategory instance for different Budgets create attempt with field value too long.
        THEN: ValidationError on .full_clean() or DataError on .create() raised.
        """
        max_length = IncomeCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            income_category = IncomeCategory(budget=budget, **payload)
            income_category.full_clean()

        assert (
            f"Ensure this value has at most {max_length} characters" in exc.value.error_dict[field_name][0].messages[0]
        )
        assert not IncomeCategory.objects.filter(budget=budget).exists()

        # .create() scenario
        with pytest.raises(DataError) as exc:
            IncomeCategory.objects.create(budget=budget, **payload)

        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not IncomeCategory.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_common_category(self, budget: Budget):
        """
        GIVEN: IncomeCategory model instance without owner created in database.
        WHEN: IncomeCategory instance create attempt without owner violating unique constraint.
        THEN: ValidationError on .full_clean() or IntegrityError on .create() raised.
        """
        payload = self.PAYLOAD.copy()
        IncomeCategory.objects.create(budget=budget, **payload)

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            income_category = IncomeCategory(budget=budget, **payload)
            income_category.full_clean()

        assert (
            "Constraint “categories_transfercategory_name_unique_when_no_owner” is violated."
            in exc.value.error_dict["__all__"][0].messages[0]
        )
        assert IncomeCategory.objects.filter(budget=budget).count() == 1

        # .create() scenario
        with pytest.raises(IntegrityError) as exc:
            IncomeCategory.objects.create(budget=budget, **payload)
        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_when_no_owner"'
            in str(exc.value)
        )
        assert IncomeCategory.objects.filter(budget=budget).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_personal_category(self, budget: Budget):
        """
        GIVEN: IncomeCategory model instance with owner created in database.
        WHEN: IncomeCategory instance create attempt with owner violating unique constraint.
        THEN: ValidationError on .full_clean() or IntegrityError on .create() raised.
        """
        payload = self.PAYLOAD.copy()
        IncomeCategory.objects.create(budget=budget, owner=budget.owner, **payload)

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            income_category = IncomeCategory(budget=budget, owner=budget.owner, **payload)
            income_category.full_clean()

        assert (
            "Constraint “categories_transfercategory_name_unique_for_owner” is violated."
            in exc.value.error_dict["__all__"][0].messages[0]
        )
        assert IncomeCategory.objects.filter(budget=budget).count() == 1

        # .create() scenario
        with pytest.raises(IntegrityError) as exc:
            IncomeCategory.objects.create(budget=budget, owner=budget.owner, **payload)
        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_for_owner"'
            in str(exc.value)
        )
        assert IncomeCategory.objects.filter(budget=budget).count() == 1
