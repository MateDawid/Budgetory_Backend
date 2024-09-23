import datetime
from decimal import Decimal

import pytest
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.transfer_category_choices import IncomeCategoryPriority
from transfers.models.transfer_model import Transfer


@pytest.mark.django_db
class TestTransferModel:
    """Tests for Transfer model"""

    INCOME_PAYLOAD = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
        "date": datetime.date(year=2024, month=9, day=1),
    }

    EXPENSE_PAYLOAD = {
        "name": "Flat rent",
        "description": "Payment for flat rent.",
        "value": Decimal(900),
        "date": datetime.date(year=2024, month=9, day=10),
    }

    def test_create_income(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Valid payload for Income proxy of Transfer model.
        WHEN: Transfer instance create attempt with valid data.
        THEN: Transfer model instance created in database with given data.
        """
        payload = self.INCOME_PAYLOAD.copy()
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = income_category_factory(budget=budget, priority=IncomeCategoryPriority.REGULAR)
        transfer = Transfer.objects.create(**payload)

        for key in payload:
            assert getattr(transfer, key) == payload[key]
        assert Transfer.objects.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 0
        assert str(transfer) == f"{transfer.date} | {transfer.category} | {transfer.value}"


#     @pytest.mark.parametrize("priority", (priority for priority in ExpenseCategoryPriority))
#     def test_create_expense_category(self, budget: Budget, priority: ExpenseCategoryPriority):
#         """
#         GIVEN: Budget model instance in database. Valid payload for EXPENSE Transfer.
#         WHEN: Transfer instance create attempt with valid data.
#         THEN: EXPENSE Transfer model instance created in database with given data.
#         """
#         payload = {
#             "name": "Expense",
#             "description": "Category for expense.",
#             "is_active": True,
#             "category_type": CategoryType.EXPENSE,
#             "priority": priority,
#         }
#         category = Transfer.objects.create(budget=budget, **payload)
#
#         for key in payload:
#             assert getattr(category, key) == payload[key]
#         assert category.owner is None
#         assert Transfer.objects.filter(budget=budget).count() == 1
#         assert Transfer.expense_categories.filter(budget=budget).count() == 1
#         assert str(category) == f"({category.category_type.label}) {category.name}"
#
#     def test_create_category_without_owner(self, budget: Budget):
#         """
#         GIVEN: Budget model instance in database. Valid payload for Transfer without owner provided.
#         WHEN: Transfer instance create attempt with valid data.
#         THEN: Transfer model instance exists in database with given data.
#         """
#         category = Transfer.objects.create(budget=budget, **self.PAYLOAD)
#
#         for key in self.PAYLOAD:
#             assert getattr(category, key) == self.PAYLOAD[key]
#         assert category.owner is None
#         assert Transfer.objects.filter(budget=budget).count() == 1
#         assert str(category) == f"({category.category_type.label}) {category.name}"
#
#     def test_create_category_with_owner(self, user_factory: FactoryMetaClass, budget: Budget):
#         """
#         GIVEN: Budget model instance in database. Valid payload for Transfer with owner provided.
#         WHEN: Transfer instance create attempt with valid data.
#         THEN: Transfer model instance exists in database with given data.
#         """
#         payload = self.PAYLOAD.copy()
#         category_owner = user_factory()
#         budget.members.add(category_owner)
#         payload["owner"] = category_owner
#
#         category = Transfer.objects.create(budget=budget, **payload)
#
#         for key in payload:
#             if key == "owner":
#                 continue
#             assert getattr(category, key) == self.PAYLOAD[key]
#         assert category.owner == category_owner
#         assert Transfer.objects.filter(budget=budget).count() == 1
#         assert str(category) == f"({category.category_type.label}) {category.name}"
#
#     def test_creating_same_category_for_two_budgets(self, budget_factory: FactoryMetaClass):
#         """
#         GIVEN: Two Budget model instances in database.
#         WHEN: Same Transfer instance for different Budgets create attempt with valid data.
#         THEN: Two Transfer model instances existing in database with given data.
#         """
#         budget_1 = budget_factory()
#         budget_2 = budget_factory()
#         payload = self.PAYLOAD.copy()
#         for budget in (budget_1, budget_2):
#             payload["budget"] = budget
#             Transfer.objects.create(**payload)
#
#         assert Transfer.objects.all().count() == 2
#         assert Transfer.objects.filter(budget=budget_1).count() == 1
#         assert Transfer.objects.filter(budget=budget_2).count() == 1
#
#     @pytest.mark.django_db(transaction=True)
#     @pytest.mark.parametrize("field_name", ["name", "description"])
#     def test_error_value_too_long(self, budget: Budget, field_name: str):
#         """
#         GIVEN: Budget model instance in database.
#         WHEN: Transfer instance create attempt with field value too long.
#         THEN: DataError raised.
#         """
#         max_length = Transfer._meta.get_field(field_name).max_length
#         payload = self.PAYLOAD.copy()
#         payload[field_name] = (max_length + 1) * "a"
#
#         with pytest.raises(DataError) as exc:
#             Transfer.objects.create(**payload)
#         assert str(exc.value) == f"value too long for type character varying({max_length})\n"
#         assert not Transfer.objects.filter(budget=budget).exists()
#
#     @pytest.mark.django_db(transaction=True)
#     @pytest.mark.parametrize("priority", (priority for priority in ExpenseCategoryPriority))
#     def test_error_invalid_priority_for_income_category_type(self, budget: Budget, priority: ExpenseCategoryPriority):
#         """
#         GIVEN: Budget model instance in database.
#         WHEN: Transfer instance create attempt with invalid priority for INCOME category_type.
#         THEN: IntegrityError raised. Transfer not created in database.
#         """
#         payload = self.PAYLOAD.copy()
#         payload["priority"] = priority
#         payload["category_type"] = CategoryType.INCOME
#
#         with pytest.raises(IntegrityError) as exc:
#             Transfer.objects.create(budget=budget, **payload)
#
#         assert (
#             'new row for relation "categories_transfercategory" violates check constraint '
#             '"categories_transfercategory_correct_priority_for_type"' in str(exc.value)
#         )
#         assert not Transfer.objects.filter(budget=budget).exists()
#
#     @pytest.mark.django_db(transaction=True)
#     def test_error_invalid_priority_for_expense_category_type(self, budget: Budget):
#         """
#         GIVEN: Budget model instance in database.
#         WHEN: Transfer instance create attempt with invalid priority for EXPENSE category_type.
#         THEN: IntegrityError raised. Transfer not created in database.
#         """
#         payload = self.PAYLOAD.copy()
#         payload["priority"] = IncomeCategoryPriority.REGULAR.value
#         payload["category_type"] = CategoryType.EXPENSE
#
#         with pytest.raises(IntegrityError) as exc:
#             Transfer.objects.create(budget=budget, **payload)
#
#         assert (
#             'new row for relation "categories_transfercategory" violates check constraint '
#             '"categories_transfercategory_correct_priority_for_type"' in str(exc.value)
#         )
#         assert not Transfer.objects.filter(budget=budget).exists()
#
#     @pytest.mark.django_db(transaction=True)
#     def test_error_not_unique_common_category(self, budget: Budget, transfer_factory: FactoryMetaClass):
#         """
#         GIVEN: Transfer model instance without owner created in database.
#         WHEN: Transfer instance create attempt without owner violating unique constraint.
#         THEN: IntegrityError raised. Transfer not created in database.
#         """
#         payload = {
#             "budget": budget,
#             "category_type": CategoryType.EXPENSE,
#             "priority": ExpenseCategoryPriority.MOST_IMPORTANT,
#             "name": "Some expense category",
#             "owner": None,
#         }
#         transfer_factory(**payload)
#
#         with pytest.raises(IntegrityError) as exc:
#             Transfer.objects.create(**payload)
#
#         assert (
#             'duplicate key value violates unique constraint "categories_transfercategory_name_unique_when_no_owner"'
#             in str(exc.value)
#         )
#         assert Transfer.objects.filter(budget=budget).count() == 1
#
#     @pytest.mark.django_db(transaction=True)
#     def test_error_not_unique_personal_category(self, budget: Budget, transfer_factory: FactoryMetaClass):
#         """
#         GIVEN: Transfer model instance with owner created in database.
#         WHEN: Transfer instance create attempt with owner violating unique constraint.
#         THEN: IntegrityError raised. Transfer not created in database.
#         """
#         payload = {
#             "budget": budget,
#             "category_type": CategoryType.EXPENSE,
#             "priority": ExpenseCategoryPriority.MOST_IMPORTANT,
#             "name": "Some expense category",
#             "owner": budget.owner,
#         }
#         transfer_factory(**payload)
#
#         with pytest.raises(IntegrityError) as exc:
#             Transfer.objects.create(**payload)
#
#         assert (
#             'duplicate key value violates unique constraint "categories_transfercategory_name_unique_for_owner"'
#             in str(exc.value)
#         )
#         assert Transfer.objects.filter(budget=budget).count() == 1
