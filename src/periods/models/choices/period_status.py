from django.db import models


class PeriodStatus(models.IntegerChoices):
    """
    Choices for Period.status field.
    """

    DRAFT = 1, "📝 Draft"
    ACTIVE = 2, "🟢 Active"
    CLOSED = 3, "🔒 Closed"
