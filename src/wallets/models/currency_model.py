from django.db import models
from django.db.models import CheckConstraint, Q


class Currency(models.Model):
    """Model for currency used in Wallet."""

    name = models.CharField(unique=True, help_text="Name of currency in ISO 4217 format.")

    class Meta:
        verbose_name_plural = "currencies"
        constraints = [
            CheckConstraint(
                check=Q(name__regex=r"^.{3}$"),
                name="currency_name_len_exact_3",
                violation_error_message="Currency name must be exactly 3 characters",
            )
        ]

    def save(self, **kwargs: dict) -> None:
        """
        Extends save method with saving Currency name in uppercase.
        """
        if self.name:
            self.name = self.name.upper()
        super(Currency, self).save()

    def __str__(self) -> str:
        return self.name
