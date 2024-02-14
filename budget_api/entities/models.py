from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Entity(models.Model):
    """Entity model for seller (or source of income) representation."""

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE, related_name='personal_entities'
    )
    is_personal = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'entities'

    def __str__(self) -> str:
        """
        Returns string representation of Entity model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return self.name

    def save(self, *args, **kwargs):
        """Override save method to clean data before saving model in database."""
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Clean Entity input data before saving in database."""
        self.clean_user()
        self.clean_name()

    def clean_name(self):
        """
        Check if Entity name is unique in global scope for not personal Entity or in user scope for personal Entity.
        """
        if self.is_personal is True and self.user.personal_entities.filter(name__iexact=self.name).exists():
            raise ValidationError('name: Personal entity with given name already exists.', code='personal-name-invalid')
        elif self.is_personal is False and Entity.objects.filter(is_personal=False, name__iexact=self.name).exists():
            raise ValidationError('user: Global entity with given name already exists.', code='global-name-invalid')

    def clean_user(self):
        """Check if user field is filled only when is_personal is set to True."""
        if self.is_personal is True and self.user is None:
            raise ValidationError(
                'user: Entity marked as personal but no user was given.', code='no-user-when-personal'
            )
        if self.is_personal is False and self.user is not None:
            raise ValidationError(
                'user: Entity marked as not personal but user was given.', code='user-when-no-personal'
            )
