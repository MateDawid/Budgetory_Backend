from django.db import models


class DepositManager(models.Manager):
    """Manager for Deposit Entities."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deposit=True)
