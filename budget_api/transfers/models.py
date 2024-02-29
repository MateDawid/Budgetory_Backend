from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class GlobalTransferCategoryManager(models.Manager):
    """Manager for global TransferCategories."""

    def get_queryset(self):
        return super().get_queryset().filter(scope=TransferCategory.GLOBAL)


class TransferCategory(models.Model):
    """TransferCategory model for grouping Transfer model instances."""

    GLOBAL = 'GLOBAL'
    PERSONAL = 'PERSONAL'
    SCOPE_CHOICES = (
        (GLOBAL, 'Global'),
        (PERSONAL, 'Personal'),
    )
    INCOME = 'INCOME'
    EXPENSE = 'EXPENSE'
    CATEGORY_TYPE_CHOICES = (
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    )

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    category_type = models.CharField(max_length=7, choices=CATEGORY_TYPE_CHOICES)
    scope = models.CharField(max_length=8, choices=SCOPE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='personal_transfer_categories',
    )
    is_active = models.BooleanField(default=True)
    objects = models.Manager()
    global_transfer_categories = GlobalTransferCategoryManager()

    class Meta:
        verbose_name_plural = 'transfer categories'

    def __str__(self) -> str:
        """
        Returns string representation of TransferCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return self.name

    def save(self, *args, **kwargs):
        """Override save method to clean data before saving model in database."""
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Clean TransferCategory input data before saving in database."""
        self.clean_user()
        self.clean_name()

    def clean_name(self):
        """
        Check if TransferCategory name is unique in global scope for global TransferCategory
        or in user scope for personal TransferCategory.
        """
        if (
            self.scope == self.PERSONAL
            and self.user.personal_transfer_categories.filter(name__iexact=self.name).exclude(id=self.id).exists()
        ):
            raise ValidationError(
                'name: Personal transfer category with given name already exists.', code='personal-name-invalid'
            )
        elif (
            self.scope == self.GLOBAL
            and TransferCategory.global_transfer_categories.filter(name__iexact=self.name).exclude(id=self.id).exists()
        ):
            raise ValidationError(
                'name: Global transfer category with given name already exists.', code='global-name-invalid'
            )

    def clean_user(self):
        """Check if user field is filled only when type is "PERSONAL"."""
        if self.scope == self.PERSONAL and self.user is None:
            raise ValidationError(
                'user: User was not provided for personal transfer category.', code='no-user-for-personal'
            )
        if self.scope == self.GLOBAL and self.user is not None:
            raise ValidationError(
                'user: User can be provided only for personal transfer category.', code='user-when-global'
            )
