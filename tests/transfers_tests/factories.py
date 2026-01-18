import random
from datetime import date, timedelta

import factory.fuzzy
from categories_tests.factories import TransferCategoryFactory
from entities_tests.factories import DepositFactory, EntityFactory
from periods_tests.factories import PeriodFactory
from wallets_tests.factories import WalletFactory

from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit, Entity
from periods.models import Period
from wallets.models import Wallet


class TransferFactory(factory.django.DjangoModelFactory):
    """Factory for Transfer model."""

    class Meta:
        model = "transfers.Transfer"

    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)
    value = factory.Faker("pyint", min_value=0, max_value=99999999)

    @factory.post_generation
    def wallet(self, create: bool, wallet: Wallet, **kwargs) -> None:
        """
        Enables to pass "wallet" as parameter to factory.

        Args:
            create [bool]: Indicates if object is created or updated.
            wallet [Wallet]: Wallet model instance.
            **kwargs [dict]: Keyword arguments
        """
        pass

    @factory.lazy_attribute
    def date(self) -> date:
        """
        Generates date field basing on given period daterange.

        Returns:
            date: Generated Transfer date.
        """
        period_value = self._Resolver__step.builder.extras.get("period")
        if period_value:
            day = random.randint(self.period.date_start.day, self.period.date_end.day)
            return date(year=self.period.date_start.year, month=self.period.date_start.month, day=day)
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            return date.today()
        last_period_dates = wallet.periods.all().order_by("date_start").values("date_start", "date_end").last()
        if not last_period_dates:
            return date.today()
        last_period_date_start, last_period_date_end = last_period_dates.values()
        return date(
            year=last_period_date_start.year,
            month=last_period_date_start.month,
            day=random.randint(last_period_date_start.day, last_period_date_end.day),
        )

    @factory.lazy_attribute
    def period(self, *args) -> Period | PeriodFactory:
        """
        Returns Period with the same Wallet as prediction category.

        Returns:
            Period | PeriodFactory: Period with the same Wallet as category.
        """
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            wallet = WalletFactory()
        date_value = self._Resolver__step.attributes.get("date")
        if not date_value:
            return PeriodFactory(wallet=wallet)
        try:
            return Period.objects.get(wallet=wallet, date_start__lte=date_value, date_end__gte=date_value)
        except Period.DoesNotExist:
            return PeriodFactory(
                wallet=wallet,
                date_start=date(year=date_value.year, month=date_value.month, day=1),
                date_end=date(
                    year=date_value.year,
                    month=date_value.month,
                    day=(
                        date(date_value.year, date_value.month + 1 if date_value.month < 12 else 1, 1)
                        - timedelta(days=1)
                    ).day,
                ),
            )

    @factory.lazy_attribute
    def entity(self, *args) -> Entity:
        """
        Returns Entity with the same Wallet as prediction period.

        Returns:
            Entity: Entity with the same Wallet as period.
        """
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            wallet = self.period.wallet
        return random.choice([None, EntityFactory(wallet=wallet)])

    @factory.lazy_attribute
    def deposit(self, *args) -> Deposit:
        """
        Returns Deposit with the same Wallet as prediction period.

        Returns:
            Deposit: Deposit with the same Wallet as period.
        """
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            wallet = self.period.wallet
        return DepositFactory(wallet=wallet)

    @factory.lazy_attribute
    def transfer_type(self, *args) -> CategoryType:
        """
        Returns the same CategoryType as set for category field or random one.

        Returns:
            CategoryType: CategoryType value.
        """
        if category := self._Resolver__step.builder.extras.get("category"):
            return category.category_type
        return random.choice([CategoryType.INCOME, CategoryType.EXPENSE])

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Wallet as prediction period.

        Returns:
            TransferCategory: TransferCategory value.
        """
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            wallet = self.period.wallet
        category_kwargs = {"wallet": wallet, "deposit": self._Resolver__step.attributes.get("deposit")}
        if transfer_type := self._Resolver__step.attributes.get("transfer_type"):
            category_kwargs["category_type"] = transfer_type
        return random.choice([None, TransferCategoryFactory(**category_kwargs)])


class IncomeFactory(TransferFactory):
    """Factory for Income proxy model."""

    class Meta:
        model = "transfers.Income"

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Wallet as prediction period and CategoryType.INCOME category_type value.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        payload = {
            "wallet": self._Resolver__step.builder.extras.get("wallet") or self.period.wallet,
            "deposit": self._Resolver__step.builder.extras.get("deposit") or self.deposit,
        }
        return random.choice([None, TransferCategoryFactory(category_type=CategoryType.INCOME, **payload)])

    @factory.lazy_attribute
    def transfer_type(self, *args) -> CategoryType:
        """
        Returns INCOME CategoryType.

        Returns:
            CategoryType: INCOME CategoryType.
        """
        return CategoryType.INCOME


class ExpenseFactory(TransferFactory):
    """Factory for Expense proxy model."""

    class Meta:
        model = "transfers.Expense"

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Wallet as prediction period and CategoryType.EXPENSE category_type value.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        payload = {
            "wallet": self._Resolver__step.builder.extras.get("wallet") or self.period.wallet,
            "deposit": self._Resolver__step.builder.extras.get("deposit") or self.deposit,
        }
        return random.choice([None, TransferCategoryFactory(category_type=CategoryType.EXPENSE, **payload)])

    @factory.lazy_attribute
    def transfer_type(self, *args) -> CategoryType:
        """
        Returns EXPENSE CategoryType.

        Returns:
            CategoryType: EXPENSE CategoryType.
        """
        return CategoryType.EXPENSE
