from django.urls import reverse


def deposits_url(budget_id):
    """Create and return Deposit detail URL."""
    return reverse("budgets:deposit-list", args=[budget_id])


def deposit_detail_url(budget_id, deposit_id):
    """Create and return Deposit detail URL."""
    return reverse("budgets:deposit-detail", args=[budget_id, deposit_id])


def entities_url(budget_id):
    """Create and return an Entity detail URL."""
    return reverse("budgets:entity-list", args=[budget_id])


def entity_detail_url(budget_id, entity_id):
    """Create and return an Entity detail URL."""
    return reverse("budgets:entity-detail", args=[budget_id, entity_id])
