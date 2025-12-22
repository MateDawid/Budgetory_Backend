"""
Django command to prepare test data.
"""

import random
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from app_users.models import User
from budgets.models import Budget, BudgetingPeriod
from budgets.models.choices.period_status import PeriodStatus
from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit, Entity
from entities.models.choices.deposit_type import DepositType
from predictions.models import ExpensePrediction
from transfers.models import Expense, Income

USER_DATA = {"email": "user@budgetory.com", "username": "User", "password": "P@ssw0rd!"}

PERIOD_2025_12_DATA = {
    "status": PeriodStatus.CLOSED,
    "name": "2025_12",
    "date_start": date(2025, 12, 1),
    "date_end": date(2025, 12, 31),
}

PERIOD_2026_01_DATA = {
    "status": PeriodStatus.CLOSED,
    "name": "2026_01",
    "date_start": date(2026, 1, 1),
    "date_end": date(2026, 1, 31),
}

PERIOD_2026_02_DATA = {
    "status": PeriodStatus.ACTIVE,
    "name": "2026_02",
    "date_start": date(2026, 2, 1),
    "date_end": date(2026, 2, 28),
}

PERIOD_2026_03_DATA = {
    "status": PeriodStatus.DRAFT,
    "name": "2026_03",
    "date_start": date(2026, 3, 1),
    "date_end": date(2026, 3, 31),
}


class Command(BaseCommand):
    """Django command to create test data."""

    objects_ids = {}

    def remove_existing_data(self):
        try:
            user = User.objects.get(email=USER_DATA["email"])
            self.stdout.write(f"Removing {USER_DATA['email']} data from database.")
            Budget.objects.filter(members=user).delete()
            user.delete()
        except User.DoesNotExist:
            pass

    def create_user(self):
        self.stdout.write(f"Creating User: {USER_DATA['email']}")
        return User.objects.create_user(**USER_DATA)

    def create_daily_expenses_budget(self, user):
        # Create Budget
        self.stdout.write("Creating Budget: Daily expenses")
        budget = Budget.objects.create(name="Daily expenses", currency="zł")
        budget.members.add(user)
        self.objects_ids["budget_id"] = budget.id
        # Create Deposits
        self.stdout.write("Creating Deposits")
        deposit_personal = Deposit.objects.create(
            budget_id=self.objects_ids["budget_id"],
            name="Users account",
            description="Account for personal User expenses and incomes.",
            deposit_type=DepositType.DAILY_EXPENSES,
        )
        deposit_common = Deposit.objects.create(
            budget_id=self.objects_ids["budget_id"],
            name="Common account",
            description="Account for common expenses and incomes.",
            deposit_type=DepositType.DAILY_EXPENSES,
        )
        # Create Entities
        self.stdout.write("Creating Entities")
        entity_employer = Entity.objects.create(budget=budget, name="Employer", description="Employer hiring User.")
        entity_buyer = Entity.objects.create(
            budget=budget, name="Buyer", description="Buyer of stuff that User's selling."
        )
        entity_food_seller = Entity.objects.create(
            budget=budget, name="Food seller", description="Seller that sells food."
        )
        entity_bills_taker = Entity.objects.create(
            budget=budget, name="Bills taker", description="Entity that receives bills."
        )
        entity_unexpected = Entity.objects.create(
            budget=budget, name="Unexpected entity", description="Entity that charges unexpectedly."
        )
        # Create Income TransferCategories for Personal Account
        self.stdout.write("Creating Income TransferCategories for Personal Account")
        personal_income_category_salary = TransferCategory.objects.create(
            budget=budget,
            name="Salary",
            description="Monthly salary.",
            deposit=deposit_personal,
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.REGULAR,
        )
        personal_income_category_sell = TransferCategory.objects.create(
            budget=budget,
            name="Sell",
            description="Cash earned from selling stuff.",
            deposit=deposit_personal,
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.REGULAR,
        )
        # Create Expense TransferCategories for Personal Account
        self.stdout.write("Creating Expense TransferCategories for Personal Account")
        personal_expense_category_food = TransferCategory.objects.create(
            budget=budget,
            name="Food",
            description="Food expenses",
            deposit=deposit_personal,
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.MOST_IMPORTANT,
        )
        personal_expense_category_transfer_to_common_account = TransferCategory.objects.create(
            budget=budget,
            name="Transfer to Common Account",
            description="Transfer to Common Account for common monthly expenses.",
            deposit=deposit_personal,
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.MOST_IMPORTANT,
        )
        personal_expense_category_unexpected = TransferCategory.objects.create(
            budget=budget,
            name="Unexpected",
            description="Unexpected expenses.",
            deposit=deposit_personal,
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.OTHERS,
        )
        # Create Income TransferCategories for Common Account
        self.stdout.write("Creating Income TransferCategories for Common Account")
        common_income_category_from_user = TransferCategory.objects.create(
            budget=budget,
            name="Transfer from User",
            description="Monthly transfer from User.",
            deposit=deposit_common,
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.REGULAR,
        )
        # Create Expense TransferCategories for Common Account
        self.stdout.write("Creating Expense TransferCategories for Common Account")
        common_expense_category_bills = TransferCategory.objects.create(
            budget=budget,
            name="Bills",
            description="Bills expenses",
            deposit=deposit_common,
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.MOST_IMPORTANT,
        )
        common_expense_category_unexpected = TransferCategory.objects.create(
            budget=budget,
            name="Unexpected",
            description="Unexpected expenses.",
            deposit=deposit_common,
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.OTHERS,
        )

        # Create BudgetingPeriods
        self.stdout.write("Creating BudgetingPeriods")
        period_2025_12 = BudgetingPeriod.objects.create(budget=budget, **PERIOD_2025_12_DATA)
        period_2026_01 = BudgetingPeriod.objects.create(budget=budget, **PERIOD_2026_01_DATA)
        period_2026_02 = BudgetingPeriod.objects.create(budget=budget, **PERIOD_2026_02_DATA)
        period_2026_03 = BudgetingPeriod.objects.create(budget=budget, **PERIOD_2026_03_DATA)
        # Create ExpensePrediction
        self.stdout.write("Creating ExpensePredictions")
        predictions = [
            # ExpensePredictions for Personal Account in 2025_12
            ExpensePrediction(
                period=period_2025_12,
                deposit=deposit_personal,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2025_12,
                deposit=deposit_personal,
                category=personal_expense_category_transfer_to_common_account,
                initial_plan=Decimal("5000.00"),
                current_plan=Decimal("5000.00"),
            ),
            ExpensePrediction(
                period=period_2025_12,
                deposit=deposit_personal,
                category=personal_expense_category_food,
                initial_plan=Decimal("1300.00"),
                current_plan=Decimal("1000.00"),
            ),
            ExpensePrediction(
                period=period_2025_12,
                deposit=deposit_personal,
                category=personal_expense_category_unexpected,
                initial_plan=Decimal("700.00"),
                current_plan=Decimal("1000.00"),
            ),
            # ExpensePredictions for Common Account in 2025_12
            ExpensePrediction(
                period=period_2025_12,
                deposit=deposit_common,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2025_12,
                deposit=deposit_common,
                category=common_expense_category_bills,
                initial_plan=Decimal("4000.00"),
                current_plan=Decimal("4000.00"),
            ),
            ExpensePrediction(
                period=period_2025_12,
                deposit=deposit_common,
                category=common_expense_category_unexpected,
                initial_plan=Decimal("1000.00"),
                current_plan=Decimal("1000.00"),
            ),
            # ExpensePredictions for Personal Account in 2026_01
            ExpensePrediction(
                period=period_2026_01,
                deposit=deposit_personal,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2026_01,
                deposit=deposit_personal,
                category=personal_expense_category_transfer_to_common_account,
                initial_plan=Decimal("5000.00"),
                current_plan=Decimal("5000.00"),
            ),
            ExpensePrediction(
                period=period_2026_01,
                deposit=deposit_personal,
                category=personal_expense_category_food,
                initial_plan=Decimal("1000.00"),
                current_plan=Decimal("1000.00"),
            ),
            ExpensePrediction(
                period=period_2026_01,
                deposit=deposit_personal,
                category=personal_expense_category_unexpected,
                initial_plan=Decimal("1100.00"),
                current_plan=Decimal("1100.00"),
            ),
            # ExpensePredictions for Common Account in 2026_01
            ExpensePrediction(
                period=period_2026_01,
                deposit=deposit_common,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2026_01,
                deposit=deposit_common,
                category=common_expense_category_bills,
                initial_plan=Decimal("4000.00"),
                current_plan=Decimal("4000.00"),
            ),
            ExpensePrediction(
                period=period_2026_01,
                deposit=deposit_common,
                category=common_expense_category_unexpected,
                initial_plan=Decimal("1000.00"),
                current_plan=Decimal("1000.00"),
            ),
            # ExpensePredictions for Personal Account in 2026_02
            ExpensePrediction(
                period=period_2026_02,
                deposit=deposit_personal,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2026_02,
                deposit=deposit_personal,
                category=personal_expense_category_transfer_to_common_account,
                initial_plan=Decimal("6000.00"),
                current_plan=Decimal("6000.00"),
            ),
            ExpensePrediction(
                period=period_2026_02,
                deposit=deposit_personal,
                category=personal_expense_category_food,
                initial_plan=Decimal("1000.00"),
                current_plan=Decimal("1000.00"),
            ),
            ExpensePrediction(
                period=period_2026_02,
                deposit=deposit_personal,
                category=personal_expense_category_unexpected,
                initial_plan=Decimal("1000.00"),
                current_plan=Decimal("1000.00"),
            ),
            # ExpensePredictions for Common Account in 2026_02
            ExpensePrediction(
                period=period_2026_02,
                deposit=deposit_common,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2026_02,
                deposit=deposit_common,
                category=common_expense_category_bills,
                initial_plan=Decimal("4000.00"),
                current_plan=Decimal("4000.00"),
            ),
            ExpensePrediction(
                period=period_2026_02,
                deposit=deposit_common,
                category=common_expense_category_unexpected,
                initial_plan=Decimal("2000.00"),
                current_plan=Decimal("2000.00"),
            ),
            # ExpensePredictions for Personal Account in 2026_03
            ExpensePrediction(
                period=period_2026_03,
                deposit=deposit_personal,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2026_03,
                deposit=deposit_personal,
                category=personal_expense_category_transfer_to_common_account,
                initial_plan=Decimal("6000.00"),
                current_plan=Decimal("6000.00"),
            ),
            ExpensePrediction(
                period=period_2026_03,
                deposit=deposit_personal,
                category=personal_expense_category_food,
                initial_plan=Decimal("1000.00"),
                current_plan=Decimal("1000.00"),
            ),
            ExpensePrediction(
                period=period_2026_03,
                deposit=deposit_personal,
                category=personal_expense_category_unexpected,
                initial_plan=Decimal("1000.00"),
                current_plan=Decimal("1000.00"),
            ),
            # ExpensePredictions for Common Account in 2026_03
            ExpensePrediction(
                period=period_2026_03,
                deposit=deposit_common,
                category=None,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ),
            ExpensePrediction(
                period=period_2026_03,
                deposit=deposit_common,
                category=common_expense_category_bills,
                initial_plan=Decimal("4000.00"),
                current_plan=Decimal("4000.00"),
            ),
            ExpensePrediction(
                period=period_2026_03,
                deposit=deposit_common,
                category=common_expense_category_unexpected,
                initial_plan=Decimal("2000.00"),
                current_plan=Decimal("2000.00"),
            ),
        ]
        ExpensePrediction.objects.bulk_create(predictions)
        # Create Incomes
        self.stdout.write("Creating Incomes")
        incomes = [
            # Incomes for Personal Account for BudgetingPeriod 2025_12
            Income(
                transfer_type=CategoryType.INCOME,
                name="Salary",
                date=date(2025, 12, 1),
                period=period_2025_12,
                value=Decimal("7000.00"),
                deposit=deposit_personal,
                entity=entity_employer,
                category=personal_income_category_salary,
                description="Salary for 2025.11",
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="Sell",
                date=date(2025, 12, 1),
                period=period_2025_12,
                value=Decimal("200.00"),
                deposit=deposit_personal,
                entity=entity_buyer,
                category=personal_income_category_sell,
                description="Selling stuff.",
            ),
            # Incomes for Common Account for BudgetingPeriod 2025_12
            Income(
                transfer_type=CategoryType.INCOME,
                name="Transfer from User",
                date=date(2025, 12, 1),
                period=period_2025_12,
                value=Decimal("5000.00"),
                deposit=deposit_common,
                entity=deposit_personal,
                category=common_income_category_from_user,
                description="Income from User for 2025.12",
            ),
            # Incomes for Personal Account for BudgetingPeriod 2026_01
            Income(
                transfer_type=CategoryType.INCOME,
                name="Salary",
                date=date(2026, 1, 1),
                period=period_2026_01,
                value=Decimal("7000.00"),
                deposit=deposit_personal,
                entity=entity_employer,
                category=personal_income_category_salary,
                description="Salary for 2025.12",
            ),
            # Incomes for Common Account for BudgetingPeriod 2026_01
            Income(
                transfer_type=CategoryType.INCOME,
                name="Transfer from User",
                date=date(2026, 1, 1),
                period=period_2026_01,
                value=Decimal("5000.00"),
                deposit=deposit_common,
                entity=deposit_personal,
                category=common_income_category_from_user,
                description="Income from User for 2026.01",
            ),
            # Incomes for Personal Account for BudgetingPeriod 2026_02
            Income(
                transfer_type=CategoryType.INCOME,
                name="Salary",
                date=date(2026, 2, 1),
                period=period_2026_02,
                value=Decimal("8000.00"),
                deposit=deposit_personal,
                entity=entity_employer,
                category=personal_income_category_salary,
                description="Salary for 2026.01",
            ),
            # Incomes for Common Account for BudgetingPeriod 2026_02
            Income(
                transfer_type=CategoryType.INCOME,
                name="Transfer from User",
                date=date(2026, 2, 1),
                period=period_2026_02,
                value=Decimal("6000.00"),
                deposit=deposit_common,
                entity=deposit_personal,
                category=common_income_category_from_user,
                description="Income from User for 2026.02",
            ),
        ]
        Income.objects.bulk_create(incomes)
        # Create Expenses
        self.stdout.write("Creating Expenses")
        expenses = [
            # Expenses for Personal Account for BudgetingPeriod 2025_12,
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Transfer to Common Account",
                date=date(2025, 12, 1),
                period=period_2025_12,
                value=Decimal("5000.00"),
                deposit=deposit_personal,
                entity=deposit_common,
                category=personal_expense_category_transfer_to_common_account,
                description="Transfer to Common Account for 2025.12",
            ),
            *[
                Expense(
                    transfer_type=CategoryType.EXPENSE,
                    name="Food",
                    date=date(2025, 12, day),
                    period=period_2025_12,
                    value=Decimal("50.00"),
                    deposit=deposit_personal,
                    entity=entity_food_seller,
                    category=personal_expense_category_food,
                    description="Something to eat.",
                )
                for day in [random.randint(number, 31) for number in range(1, 21)]
            ],
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Unexpected",
                date=date(2025, 12, 5),
                period=period_2025_12,
                value=Decimal("200.00"),
                deposit=deposit_personal,
                entity=entity_unexpected,
                category=personal_expense_category_unexpected,
                description="Not expected expense",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Unexpected",
                date=date(2025, 12, 10),
                period=period_2025_12,
                value=Decimal("500.00"),
                deposit=deposit_personal,
                entity=entity_unexpected,
                category=personal_expense_category_unexpected,
                description="Not expected expense",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Not categorized",
                date=date(2025, 12, 15),
                period=period_2025_12,
                value=Decimal("200.00"),
                deposit=deposit_personal,
                entity=None,
                category=None,
                description="Not categorized expense",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Not categorized",
                date=date(2025, 12, 20),
                period=period_2025_12,
                value=Decimal("200.00"),
                deposit=deposit_personal,
                entity=None,
                category=None,
                description="Not categorized expense",
            ),
            # Expenses for Common Account for BudgetingPeriod 2025_12,
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Flat",
                date=date(2025, 12, 1),
                period=period_2025_12,
                value=Decimal("2000.00"),
                deposit=deposit_common,
                entity=entity_bills_taker,
                category=common_expense_category_bills,
                description="Bill for flat.",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Energy",
                date=date(2025, 12, 1),
                period=period_2025_12,
                value=Decimal("2000.00"),
                deposit=deposit_common,
                entity=entity_bills_taker,
                category=common_expense_category_bills,
                description="Bill for energy.",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Unexpected",
                date=date(2025, 12, 15),
                period=period_2025_12,
                value=Decimal("800.00"),
                deposit=deposit_common,
                entity=entity_unexpected,
                category=common_expense_category_unexpected,
                description="Unexpected expense.",
            ),
            # Expenses for Personal Account for BudgetingPeriod 2026_01
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Transfer to Common Account",
                date=date(2026, 1, 1),
                period=period_2026_01,
                value=Decimal("5000.00"),
                deposit=deposit_personal,
                entity=deposit_common,
                category=personal_expense_category_transfer_to_common_account,
                description="Transfer to Common Account for 2026.01",
            ),
            *[
                Expense(
                    transfer_type=CategoryType.EXPENSE,
                    name="Food",
                    date=date(2026, 1, day),
                    period=period_2026_01,
                    value=Decimal("50.00"),
                    deposit=deposit_personal,
                    entity=entity_food_seller,
                    category=personal_expense_category_food,
                    description="Something to eat.",
                )
                for day in [random.randint(number, 31) for number in range(1, 23)]
            ],
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Unexpected",
                date=date(2026, 1, 15),
                period=period_2026_01,
                value=Decimal("500.00"),
                deposit=deposit_personal,
                entity=entity_unexpected,
                category=personal_expense_category_unexpected,
                description="Not expected expense",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Not categorized",
                date=date(2026, 1, 20),
                period=period_2026_01,
                value=Decimal("200.00"),
                deposit=deposit_personal,
                entity=None,
                category=None,
                description="Not categorized expense",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Not categorized",
                date=date(2026, 1, 30),
                period=period_2026_01,
                value=Decimal("300.00"),
                deposit=deposit_personal,
                entity=None,
                category=None,
                description="Not categorized expense",
            ),
            # Expenses for Common Account for BudgetingPeriod 2026_01
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Flat",
                date=date(2026, 1, 1),
                period=period_2026_01,
                value=Decimal("2000.00"),
                deposit=deposit_common,
                entity=entity_bills_taker,
                category=common_expense_category_bills,
                description="Bill for flat.",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Energy",
                date=date(2026, 1, 1),
                period=period_2026_01,
                value=Decimal("2000.00"),
                deposit=deposit_common,
                entity=entity_bills_taker,
                category=common_expense_category_bills,
                description="Bill for energy.",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Unexpected",
                date=date(2026, 1, 16),
                period=period_2026_01,
                value=Decimal("800.00"),
                deposit=deposit_common,
                entity=entity_unexpected,
                category=common_expense_category_unexpected,
                description="Unexpected expense.",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Unexpected",
                date=date(2026, 1, 27),
                period=period_2026_01,
                value=Decimal("400.00"),
                deposit=deposit_common,
                entity=entity_unexpected,
                category=common_expense_category_unexpected,
                description="Unexpected expense.",
            ),
            # Expenses for Personal Account for BudgetingPeriod 2026_02
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Transfer to Common Account",
                date=date(2026, 2, 1),
                period=period_2026_02,
                value=Decimal("6000.00"),
                deposit=deposit_personal,
                entity=deposit_common,
                category=personal_expense_category_transfer_to_common_account,
                description="Transfer to Common Account for 2026.02",
            ),
            *[
                Expense(
                    transfer_type=CategoryType.EXPENSE,
                    name="Food",
                    date=date(2026, 2, day),
                    period=period_2026_02,
                    value=Decimal("50.00"),
                    deposit=deposit_personal,
                    entity=entity_food_seller,
                    category=personal_expense_category_food,
                    description="Something to eat.",
                )
                for day in [random.randint(number, 28) for number in range(1, 11)]
            ],
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Unexpected",
                date=date(2026, 2, 15),
                period=period_2026_02,
                value=Decimal("500.00"),
                deposit=deposit_personal,
                entity=entity_unexpected,
                category=personal_expense_category_unexpected,
                description="Not expected expense",
            ),
            # Expenses for Common Account for BudgetingPeriod 2026_02
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Flat",
                date=date(2026, 2, 1),
                period=period_2026_02,
                value=Decimal("2000.00"),
                deposit=deposit_common,
                entity=entity_bills_taker,
                category=common_expense_category_bills,
                description="Bill for flat.",
            ),
            Expense(
                transfer_type=CategoryType.EXPENSE,
                name="Energy",
                date=date(2026, 2, 1),
                period=period_2026_02,
                value=Decimal("3000.00"),
                deposit=deposit_common,
                entity=entity_bills_taker,
                category=common_expense_category_bills,
                description="Bill for energy.",
            ),
        ]
        Expense.objects.bulk_create(expenses)

    def handle(self, *args, **options):
        """Entrypoint for command."""
        with transaction.atomic():
            self.remove_existing_data()
            user = self.create_user()
            self.create_daily_expenses_budget(user)
