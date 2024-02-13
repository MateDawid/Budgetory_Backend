from django.conf import settings
from django.db import models


class Entity(models.Model):
    """Entity model for seller (or source of income) representation."""

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='personal_entities'
    )
    is_personal = models.BooleanField(default=False)

    def __str__(self) -> str:
        """
        Returns string representation of Entity model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return self.name
