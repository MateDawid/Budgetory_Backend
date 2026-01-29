from app_users.models import User
from app_users.services.demo_login_service.factories.entities import create_deposits_and_entities
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
        self.deposits = {}
        self.entities = {}

    def create_initial_data_for_demo_user(self) -> None:
        """
        Main function of DemoUserInitialDataService. Creates initial data for demo user.
        """
        self.create_demo_wallets()
        self.create_demo_entities()

    def create_demo_wallets(self) -> None:
        """
        Creates Wallets for demo User.
        """
        daily_wallet, long_term_wallet = create_wallets()
        daily_wallet.members.add(self.user)
        long_term_wallet.members.add(self.user)
        self.wallets[daily_wallet.name] = daily_wallet
        self.wallets[long_term_wallet.name] = long_term_wallet

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

    # def create_categories_entities(self):
    #     """
    #     Creates Categories for demo User.
    #     """
    #     categories = create_categories(deposits=self.deposits)
