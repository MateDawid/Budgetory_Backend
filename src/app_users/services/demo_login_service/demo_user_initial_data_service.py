from app_users.models import User
from app_users.services.demo_login_service.factories.categories import create_categories
from app_users.services.demo_login_service.factories.entities import create_deposits_and_entities
from app_users.services.demo_login_service.factories.periods import create_periods
from app_users.services.demo_login_service.factories.predictions import create_predictions
from app_users.services.demo_login_service.factories.wallets import WalletName, create_wallets


class DemoUserInitialDataService:
    """
    Service to create initial data for demo User.
    """

    def __init__(self, user):
        """
        Saves demo User and inits dicts storing created objects in class context.

        Args:
            user (User): Demo User for which data will be created.
        """
        self.user: User = user
        self.wallets = {}
        self.daily_wallet_periods = {}
        self.long_term_wallet_periods = {}
        self.deposits = {}
        self.entities = {}
        self.income_categories = {}
        self.expense_categories = {}

    def create_initial_data_for_demo_user(self) -> None:
        """
        Main function of DemoUserInitialDataService. Creates initial data for demo user.
        """
        self.create_demo_wallets()
        self.create_demo_periods()
        self.create_demo_entities()
        self.create_demo_categories()
        self.create_demo_predictions()

    def create_demo_wallets(self) -> None:
        """
        Creates Wallets for demo User.
        """
        daily_wallet, long_term_wallet = create_wallets()
        daily_wallet.members.add(self.user)
        long_term_wallet.members.add(self.user)
        self.wallets[daily_wallet.name] = daily_wallet
        self.wallets[long_term_wallet.name] = long_term_wallet

    def create_demo_periods(self):
        """
        Creates Periods for demo User.
        """
        daily_wallet_periods, long_term_wallet_periods = create_periods(
            daily_wallet=self.wallets[WalletName.DAILY], long_term_wallet=self.wallets[WalletName.LONG_TERM]
        )
        for daily_wallet_period in daily_wallet_periods:
            self.daily_wallet_periods[daily_wallet_period.name] = daily_wallet_period
        for long_term_wallet_period in long_term_wallet_periods:
            self.long_term_wallet_periods[long_term_wallet_period.name] = long_term_wallet_period

    def create_demo_entities(self) -> None:
        """
        Creates Deposits and Entities for demo User.
        """
        deposits, entities = create_deposits_and_entities(
            daily_wallet=self.wallets[WalletName.DAILY], long_term_wallet=self.wallets[WalletName.LONG_TERM]
        )
        for deposit in deposits:
            self.deposits[deposit.name] = deposit
        for entity in entities:
            self.entities[entity.name] = entity

    def create_demo_categories(self):
        """
        Creates Categories for demo User.
        """
        income_categories, expense_categories = create_categories(deposits=self.deposits)
        for income_category in income_categories:
            self.income_categories[income_category.name] = income_category
        for expense_category in expense_categories:
            self.expense_categories[expense_category.name] = expense_category

    def create_demo_predictions(self):
        """
        Creates Predictions for demo User.
        """
        create_predictions(
            daily_wallet_periods=self.daily_wallet_periods,
            deposits=self.deposits,
            expense_categories=self.expense_categories,
        )

    def create_demo_incomes(self):
        """
        Creates Incomes for demo User.
        """
        ...

    def create_demo_expenses(self):
        """
        Creates Expenses for demo User.
        """
        ...
