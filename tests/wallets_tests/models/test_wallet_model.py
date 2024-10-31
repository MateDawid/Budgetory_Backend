import pytest
from django.db import DataError, IntegrityError

from budgets.models.budget_model import Budget
from wallets.models import Wallet


@pytest.mark.django_db
class TestWalletModel:
    """Tests for Wallet model"""

    PAYLOAD: dict = {"name": "General wallet"}

    def test_create_wallet(self, budget: Budget):
        """
        GIVEN: Budget model instance in database. Valid payload for Wallet provided.
        WHEN: Wallet instance create attempt with valid data.
        THEN: Wallet model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["budget"] = budget

        wallet = Wallet.objects.create(**payload)

        for key in payload:
            assert getattr(wallet, key) == payload[key]
        assert Wallet.objects.all().count() == 1
        assert str(wallet) == f"{wallet.name} ({wallet.budget.name})"

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, budget: Budget):
        """
        GIVEN: Budget model instances in database.
        WHEN: Wallet instance create attempt with description value too long.
        THEN: DataError raised.
        """
        max_length = Wallet._meta.get_field("name").max_length
        payload = self.PAYLOAD.copy()
        payload["budget"] = budget
        payload["name"] = (max_length + 1) * "a"

        with pytest.raises(DataError) as exc:
            Wallet.objects.create(**payload)

        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Wallet.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, budget: Budget):
        """
        GIVEN: Single Wallet for Budget in database.
        WHEN: Wallet instance create attempt with name already used for existing Wallet.
        THEN: DataError raised, object not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["budget"] = budget
        Wallet.objects.create(**payload)

        with pytest.raises(IntegrityError) as exc:
            Wallet.objects.create(**payload)

        assert f'DETAIL:  Key (name, budget_id)=({payload["name"]}, {budget.id}) already exists.' in str(exc.value)
        assert Wallet.objects.filter(budget=budget).count() == 1
