from django.db import models


class DepositType(models.IntegerChoices):
    """
    Choices for Deposit.deposit_type field.
    """

    DAILY_EXPENSES = 1, "💸 For daily expenses"
    SAVINGS = 2, "💰 For savings"
    INVESTMENTS = 3, "🪙 For investments"
    OTHER = 4, "❔ Other"
