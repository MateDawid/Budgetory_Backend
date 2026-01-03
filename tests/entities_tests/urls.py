from django.urls import reverse


def deposits_url(wallet_id):
    """Create and return Deposit detail URL."""
    return reverse("wallets:deposit-list", args=[wallet_id])


def deposit_detail_url(wallet_id, deposit_id):
    """Create and return Deposit detail URL."""
    return reverse("wallets:deposit-detail", args=[wallet_id, deposit_id])


def entities_url(wallet_id):
    """Create and return an Entity detail URL."""
    return reverse("wallets:entity-list", args=[wallet_id])


def entity_detail_url(wallet_id, entity_id):
    """Create and return an Entity detail URL."""
    return reverse("wallets:entity-detail", args=[wallet_id, entity_id])
