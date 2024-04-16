from django.db import models


class BaseTransferModel(models.Model):
    """Base for models sharing TransferTypes choices."""

    class TransferTypes(models.IntegerChoices):
        """Choices for deposit_type value."""

        INCOME = 0, 'Income'
        EXPENSE = 1, 'Expense'
        RELOCATION = 2, 'Relocation'

    class Meta:
        abstract = True
