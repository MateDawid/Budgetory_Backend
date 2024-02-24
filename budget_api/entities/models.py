from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class GlobalEntityManager(models.Manager):
    """Manager for global Entities."""

    def get_queryset(self):
        return super().get_queryset().filter(type=Entity.GLOBAL)


class Entity(models.Model):
    """Entity model for seller (or source of income) representation."""

    GLOBAL = 'GLOBAL'
    PERSONAL = 'PERSONAL'

    TYPE_CHOICES = (
        (GLOBAL, 'Global'),
        (PERSONAL, 'Personal'),
    )

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE, related_name='personal_entities'
    )
    type = models.CharField(max_length=8, choices=TYPE_CHOICES)

    objects = models.Manager()
    global_entities = GlobalEntityManager()

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
        if (
            self.type == self.PERSONAL
            and self.user.personal_entities.filter(name__iexact=self.name).exclude(id=self.id).exists()
        ):
            raise ValidationError('name: Personal entity with given name already exists.', code='personal-name-invalid')
        elif (
            self.type == self.GLOBAL
            and Entity.global_entities.filter(name__iexact=self.name).exclude(id=self.id).exists()
        ):
            raise ValidationError('name: Global entity with given name already exists.', code='global-name-invalid')

    def clean_user(self):
        """Check if user field is filled only when type is "PERSONAL"."""
        if self.type == self.PERSONAL and self.user is None:
            raise ValidationError('user: User was not provided for personal Entity.', code='no-user-for-personal')
        if self.type == self.GLOBAL and self.user is not None:
            raise ValidationError('user: User can be provided only for personal Entities.', code='user-when-global')
