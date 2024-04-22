from django.conf import settings
from django.db import models


class TransferCategory(models.Model):
    """TransferCategory model for grouping Transfer model instances."""

    group = models.ForeignKey(
        'transfers.TransferCategoryGroup', blank=False, null=False, on_delete=models.CASCADE, related_name='categories'
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='personal_categories',
    )
    is_active = models.BooleanField(default=True)

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

    # def clean(self):
    #     """Clean TransferCategory input data before saving in database."""
    #     self.clean_owner()
    #     self.clean_name()
    #
    # def clean_name(self):
    #     if (
    #         self.scope == self.PERSONAL
    #         and self.user.personal_transfer_categories.filter(name__iexact=self.name).exclude(id=self.id).exists()
    #     ):
    #         raise ValidationError(
    #             'name: Personal transfer category with given name already exists.', code='personal-name-invalid'
    #         )
    #     elif (
    #         self.scope == self.GLOBAL
    #         and TransferCategory.global_transfer_categories.filter(name__iexact=self.name).exclude(
    #         id=self.id).exists()
    #     ):
    #         raise ValidationError(
    #             'name: Global transfer category with given name already exists.', code='global-name-invalid'
    #         )
    #
    # def clean_owner(self):
    #     """Check if user field is filled only when type is "PERSONAL"."""
    #     if self.scope == self.PERSONAL and self.user is None:
    #         raise ValidationError(
    #             'user: User was not provided for personal transfer category.', code='no-user-for-personal'
    #         )
    #     if self.scope == self.GLOBAL and self.user is not None:
    #         raise ValidationError(
    #             'user: User can be provided only for personal transfer category.', code='user-when-global'
    #         )
