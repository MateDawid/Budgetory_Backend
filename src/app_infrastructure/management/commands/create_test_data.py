"""
Django command to prepare test data.
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from app_users.models import User
from app_users.services.demo_login_service.demo_user_initial_data_service import DemoUserInitialDataService
from periods.models.choices.period_status import PeriodStatus

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

    def remove_existing_data(self):
        try:
            user = User.objects.get(email=USER_DATA["email"])
            self.stdout.write(f"Removing {USER_DATA['email']} data from database.")
            user.delete()
        except User.DoesNotExist:
            pass

    def create_user(self) -> User:
        self.stdout.write(f"Creating User: {USER_DATA['email']}")
        return User.objects.create_user(**USER_DATA)

    def create_data(self, user: User) -> None:
        self.stdout.write(f"Creating data for User: {USER_DATA['email']}")
        service = DemoUserInitialDataService(user=user)
        service.create_initial_data_for_demo_user()

    def handle(self, *args, **options):
        """Entrypoint for command."""
        with transaction.atomic():
            self.remove_existing_data()
            user = self.create_user()
            self.create_data(user)
