import pytest
from categories_tests.utils import INVALID_TYPE_AND_PRIORITY_COMBINATIONS, VALID_TYPE_AND_PRIORITY_COMBINATIONS
from django.db import DataError, IntegrityError
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from categories.models.transfer_category_model import TransferCategory


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
    def test_create_transfer_category(
        self, budget: Budget, category_type: CategoryType, priority: CategoryPriority, deposit_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database. Valid payload for TransferCategory.
        WHEN: TransferCategory instance create attempt with valid data.
        THEN: TransferCategory model instance created in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority
        payload["deposit"] = deposit_factory(budget=budget)

        category = TransferCategory.objects.create(budget=budget, **payload)

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        assert str(category) == f"({category_type.label}) {category.name}"

    @pytest.mark.parametrize("category_type, priority", VALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_save_transfer_category(
        self, budget: Budget, category_type: CategoryType, priority: CategoryPriority, deposit_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategory instance save attempt with valid data.
        THEN: TransferCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority
        payload["deposit"] = deposit_factory(budget=budget)

        category = TransferCategory(budget=budget, **payload)
        category.full_clean()
        category.save()
        category.refresh_from_db()

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        assert str(category) == f"({category_type.label}) {category.name}"

    def test_creating_same_category_for_two_budgets(
        self, budget_factory: FactoryMetaClass, deposit_factory: FactoryMetaClass
    ):
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
            payload["deposit"] = deposit_factory(budget=budget)
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
        self,
        budget: Budget,
        deposit_factory: FactoryMetaClass,
        category_type: CategoryType,
        priority: CategoryPriority,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategory instance create attempt with invalid priority for category_type.
        THEN: IntegrityError raised. TransferCategory not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["priority"] = priority
        payload["category_type"] = category_type
        payload["deposit"] = deposit_factory(budget=budget)

        with pytest.raises(IntegrityError) as exc:
            TransferCategory.objects.create(budget=budget, **payload)

        assert (
            'new row for relation "categories_transfercategory" violates check constraint '
            '"categories_transfercategory_correct_priority_for_type"' in str(exc.value)
        )
        assert not TransferCategory.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_category(
        self, budget: Budget, deposit_factory: FactoryMetaClass, transfer_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: TransferCategory model instance created in database.
        WHEN: TransferCategory instance create attempt violating unique constraint.
        THEN: IntegrityError raised. TransferCategory not created in database.
        """
        payload: dict = self.PAYLOAD.copy()
        payload["budget"] = budget
        payload["deposit"] = deposit_factory(budget=budget)
        transfer_category_factory(**payload)

        with pytest.raises(IntegrityError) as exc:
            TransferCategory.objects.create(**payload)

        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_for_deposit"'
            in str(exc.value)
        )
        assert TransferCategory.objects.filter(budget=budget).count() == 1
