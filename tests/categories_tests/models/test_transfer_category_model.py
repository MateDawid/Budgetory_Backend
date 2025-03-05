import pytest
from django.db import DataError, IntegrityError
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from categories.models.transfer_category_model import TransferCategory

VALID_TYPE_AND_PRIORITY_COMBINATIONS = (
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.REGULAR,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.REGULAR.label}",
    ),
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.IRREGULAR,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.IRREGULAR.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.MOST_IMPORTANT,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.MOST_IMPORTANT.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE, CategoryPriority.DEBTS, id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.DEBTS.label}"
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.SAVINGS,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.SAVINGS.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.OTHERS,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.OTHERS.label}",
    ),
)

INVALID_TYPE_AND_PRIORITY_COMBINATIONS = (
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.REGULAR,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.REGULAR.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.IRREGULAR,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.IRREGULAR.label}",
    ),
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.MOST_IMPORTANT,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.MOST_IMPORTANT.label}",
    ),
    pytest.param(
        CategoryType.INCOME, CategoryPriority.DEBTS, id=f"{CategoryType.INCOME.label}-{CategoryPriority.DEBTS.label}"
    ),
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.SAVINGS,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.SAVINGS.label}",
    ),
    pytest.param(
        CategoryType.INCOME, CategoryPriority.OTHERS, id=f"{CategoryType.INCOME.label}-{CategoryPriority.OTHERS.label}"
    ),
)


@pytest.mark.django_db
class TestTransferCategoryModel:
    """Tests for TransferCategory model"""

    PAYLOAD = {
        "name": "Category name",
        "description": "Category description.",
        "is_active": True,
        "category_type": CategoryType.EXPENSE,
        "priority": CategoryPriority.MOST_IMPORTANT,
    }

    @pytest.mark.parametrize("category_type, priority", VALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_create_transfer_category(self, budget: Budget, category_type: CategoryType, priority: CategoryPriority):
        """
        GIVEN: Budget model instance in database. Valid payload for TransferCategory.
        WHEN: TransferCategory instance create attempt with valid data.
        THEN: TransferCategory model instance created in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority

        category = TransferCategory.objects.create(budget=budget, **payload)

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        assert str(category) == f"({category_type.label}) {category.name}"

    @pytest.mark.parametrize("category_type, priority", VALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_save_transfer_category(self, budget: Budget, category_type: CategoryType, priority: CategoryPriority):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategory instance save attempt with valid data.
        THEN: TransferCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority

        category = TransferCategory(budget=budget, **payload)
        category.full_clean()
        category.save()
        category.refresh_from_db()

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        assert str(category) == f"({category_type.label}) {category.name}"

    def test_create_category_without_owner(self, budget: Budget):
        """
        GIVEN: Budget model instance in database. Valid payload for TransferCategory without owner provided.
        WHEN: TransferCategory instance create attempt with valid data.
        THEN: TransferCategory model instance exists in database with given data.
        """
        category = TransferCategory.objects.create(budget=budget, owner=None, **self.PAYLOAD)

        assert TransferCategory.objects.filter(budget=budget).count() == 1
        for key in self.PAYLOAD:
            assert getattr(category, key) == self.PAYLOAD[key]
        assert category.owner is None

    def test_create_category_with_owner(self, user_factory: FactoryMetaClass, budget: Budget):
        """
        GIVEN: Budget model instance in database. Valid payload for TransferCategory with owner provided.
        WHEN: TransferCategory instance create attempt with valid data.
        THEN: TransferCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        category_owner = user_factory()
        budget.members.add(category_owner)
        payload["owner"] = category_owner

        category = TransferCategory.objects.create(budget=budget, **payload)

        for key in payload:
            if key == "owner":
                continue
            assert getattr(category, key) == self.PAYLOAD[key]
        assert category.owner == category_owner
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        assert str(category) == f"({category.category_type.label}) {category.name}"

    def test_creating_same_category_for_two_budgets(self, budget_factory: FactoryMetaClass):
        """
        GIVEN: Two Budget model instances in database.
        WHEN: Same TransferCategory instance for different Budgets create attempt with valid data.
        THEN: Two TransferCategory model instances existing in database with given data.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        payload = self.PAYLOAD.copy()
        for budget in (budget_1, budget_2):
            payload["budget"] = budget
            TransferCategory.objects.create(**payload)

        assert TransferCategory.objects.all().count() == 2
        assert TransferCategory.objects.filter(budget=budget_1).count() == 1
        assert TransferCategory.objects.filter(budget=budget_2).count() == 1

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(self, budget: Budget, field_name: str):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategory instance create attempt with field value too long.
        THEN: DataError raised.
        """
        max_length = TransferCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        with pytest.raises(DataError) as exc:
            TransferCategory.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not TransferCategory.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("category_type, priority", INVALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_error_invalid_priority_for_category_type(
        self, budget: Budget, category_type: CategoryType, priority: CategoryPriority
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategory instance create attempt with invalid priority for category_type.
        THEN: IntegrityError raised. TransferCategory not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["priority"] = priority
        payload["category_type"] = category_type

        with pytest.raises(IntegrityError) as exc:
            TransferCategory.objects.create(budget=budget, **payload)

        assert (
            'new row for relation "categories_transfercategory" violates check constraint '
            '"categories_transfercategory_correct_priority_for_type"' in str(exc.value)
        )
        assert not TransferCategory.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_common_category(self, budget: Budget, transfer_category_factory: FactoryMetaClass):
        """
        GIVEN: TransferCategory model instance without owner created in database.
        WHEN: TransferCategory instance create attempt without owner violating unique constraint.
        THEN: IntegrityError raised. TransferCategory not created in database.
        """
        payload: dict = self.PAYLOAD.copy()
        payload["budget"] = budget
        payload["owner"] = None
        transfer_category_factory(**payload)

        with pytest.raises(IntegrityError) as exc:
            TransferCategory.objects.create(**payload)

        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_when_no_owner"'
            in str(exc.value)
        )
        assert TransferCategory.objects.filter(budget=budget).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_personal_category(self, budget: Budget, transfer_category_factory: FactoryMetaClass):
        """
        GIVEN: TransferCategory model instance with owner created in database.
        WHEN: TransferCategory instance create attempt with owner violating unique constraint.
        THEN: IntegrityError raised. TransferCategory not created in database.
        """
        payload: dict = self.PAYLOAD.copy()
        payload["budget"] = budget
        payload["owner"] = budget.members.first()
        transfer_category_factory(**payload)

        with pytest.raises(IntegrityError) as exc:
            TransferCategory.objects.create(**payload)

        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_for_owner"'
            in str(exc.value)
        )
        assert TransferCategory.objects.filter(budget=budget).count() == 1
