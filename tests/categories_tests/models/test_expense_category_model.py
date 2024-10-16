import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError

from budgets.models import Budget
from categories.models.expense_category_model import ExpenseCategory
from categories.models.transfer_category_choices import CategoryType, ExpenseCategoryPriority


@pytest.mark.django_db
class TestExpenseCategoryModel:
    """Tests for ExpenseCategory proxy model"""

    PAYLOAD = {
        "name": "Bills",
        "description": "Category for bills.",
        "is_active": True,
        "priority": ExpenseCategoryPriority.MOST_IMPORTANT,
    }

    def test_save_expense_category(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategory instance save attempt with valid data.
        THEN: ExpenseCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()

        expense_category = ExpenseCategory(budget=budget, **payload)
        expense_category.full_clean()
        expense_category.save()
        expense_category.refresh_from_db()

        for key in payload:
            assert getattr(expense_category, key) == payload[key]
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1
        assert expense_category.category_type == CategoryType.EXPENSE
        assert str(expense_category) == f"({expense_category.category_type.label}) {expense_category.name}"

    def test_create_expense_category(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategory instance create attempt with valid data.
        THEN: ExpenseCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()

        expense_category = ExpenseCategory.objects.create(budget=budget, **payload)

        for key in payload:
            assert getattr(expense_category, key) == payload[key]
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1
        assert expense_category.category_type == CategoryType.EXPENSE
        assert str(expense_category) == f"({expense_category.category_type.label}) {expense_category.name}"

    def test_proper_category_type_on_expense_category_save(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategory instance save attempt with category_type=CategoryType.INCOME in payload.
        THEN: ExpenseCategory model instance exists in database with category_type=CategoryType.EXPENSE.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = CategoryType.INCOME.value

        expense_category = ExpenseCategory(budget=budget, **payload)
        expense_category.full_clean()
        expense_category.save()

        assert ExpenseCategory.objects.filter(budget=budget).count() == 1
        assert expense_category.category_type == CategoryType.EXPENSE

    def test_proper_category_type_on_expense_category_create(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategory instance create attempt with category_type=CategoryType.INCOME in payload.
        THEN: ExpenseCategory model instance exists in database category_type=CategoryType.EXPENSE.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = CategoryType.INCOME.value

        expense_category = ExpenseCategory.objects.create(budget=budget, **payload)

        assert ExpenseCategory.objects.filter(budget=budget).count() == 1
        assert expense_category.category_type == CategoryType.EXPENSE

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(self, budget: Budget, field_name: str):
        """
        GIVEN: Budget model instances in database.
        WHEN: ExpenseCategory instance for different Budgets create attempt with field value too long.
        THEN: ValidationError on .full_clean() or DataError on .create() raised.
        """
        max_length = ExpenseCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            expense_category = ExpenseCategory(budget=budget, **payload)
            expense_category.full_clean()

        assert (
            f"Ensure this value has at most {max_length} characters" in exc.value.error_dict[field_name][0].messages[0]
        )
        assert not ExpenseCategory.objects.filter(budget=budget).exists()

        # .create() scenario
        with pytest.raises(DataError) as exc:
            ExpenseCategory.objects.create(budget=budget, **payload)

        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not ExpenseCategory.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_common_category(self, budget: Budget):
        """
        GIVEN: ExpenseCategory model instance without owner created in database.
        WHEN: ExpenseCategory instance create attempt without owner violating unique constraint.
        THEN: ValidationError on .full_clean() or IntegrityError on .create() raised.
        """
        payload = self.PAYLOAD.copy()
        ExpenseCategory.objects.create(budget=budget, **payload)

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            expense_category = ExpenseCategory(budget=budget, **payload)
            expense_category.full_clean()

        assert (
            "Constraint “categories_transfercategory_name_unique_when_no_owner” is violated."
            in exc.value.error_dict["__all__"][0].messages[0]
        )
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1

        # .create() scenario
        with pytest.raises(IntegrityError) as exc:
            ExpenseCategory.objects.create(budget=budget, **payload)
        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_when_no_owner"'
            in str(exc.value)
        )
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_personal_category(self, budget: Budget):
        """
        GIVEN: ExpenseCategory model instance with owner created in database.
        WHEN: ExpenseCategory instance create attempt with owner violating unique constraint.
        THEN: ValidationError on .full_clean() or IntegrityError on .create() raised.
        """
        payload = self.PAYLOAD.copy()
        ExpenseCategory.objects.create(budget=budget, owner=budget.owner, **payload)

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            expense_category = ExpenseCategory(budget=budget, owner=budget.owner, **payload)
            expense_category.full_clean()

        assert (
            "Constraint “categories_transfercategory_name_unique_for_owner” is violated."
            in exc.value.error_dict["__all__"][0].messages[0]
        )
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1

        # .create() scenario
        with pytest.raises(IntegrityError) as exc:
            ExpenseCategory.objects.create(budget=budget, owner=budget.owner, **payload)
        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_for_owner"'
            in str(exc.value)
        )
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1
