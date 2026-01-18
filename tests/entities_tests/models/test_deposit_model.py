import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError

from entities.models.deposit_model import Deposit
from wallets.models.wallet_model import Wallet


@pytest.mark.django_db
class TestDepositModel:
    """Tests for Deposit model"""

    PAYLOAD: dict = {
        "name": "Bank account",
        "description": "My own bank account",
        "is_active": True,
        "is_deposit": True,
    }

    def test_save_deposit(self, wallet: Wallet):
        """
        GIVEN: Wallet model instance in database.
        WHEN: Deposit instance save attempt with valid data.
        THEN: Deposit model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["wallet"] = wallet

        deposit = Deposit(**payload)
        deposit.full_clean()
        deposit.save()

        for key in payload:
            assert getattr(deposit, key) == payload[key]
        assert Deposit.objects.filter(wallet=wallet).count() == 1
        assert deposit.is_deposit is True
        assert str(deposit) == f"{deposit.name} ({deposit.wallet.name})"

    def test_create_deposit(self, wallet: Wallet):
        """
        GIVEN: Wallet model instance in database.
        WHEN: Deposit instance create attempt with valid data.
        THEN: Deposit model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["wallet"] = wallet

        deposit = Deposit.objects.create(**payload)

        for key in payload:
            assert getattr(deposit, key) == payload[key]
        assert Deposit.objects.filter(wallet=wallet).count() == 1
        assert deposit.is_deposit is True
        assert str(deposit) == f"{deposit.name} ({deposit.wallet.name})"

    def test_is_deposit_true_on_deposit_create(self, wallet: Wallet):
        """
        GIVEN: Wallet model instance in database.
        WHEN: Deposit instance create attempt with is_deposit=False in payload.
        THEN: Deposit model instance exists in database with is_deposit=True.
        """
        payload = self.PAYLOAD.copy()
        payload["wallet"] = wallet
        payload["is_deposit"] = False

        deposit = Deposit.objects.create(**payload)

        assert Deposit.objects.filter(wallet=wallet).count() == 1
        assert deposit.is_deposit is True

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(self, wallet: Wallet, field_name: str):
        """
        GIVEN: Wallet model instances in database.
        WHEN: Deposit instance for different Wallets create attempt with field value too long.
        THEN: ValidationError on .full_clean() or DataError on .create() raised.
        """
        max_length = Deposit._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload["wallet"] = wallet
        payload[field_name] = (max_length + 1) * "a"

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            deposit = Deposit(**payload)
            deposit.full_clean()

        assert (
            f"Ensure this value has at most {max_length} characters" in exc.value.error_dict[field_name][0].messages[0]
        )
        assert not Deposit.objects.filter(wallet=wallet).exists()

        # .create() scenario
        with pytest.raises(DataError) as exc:
            Deposit.objects.create(**payload)

        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Deposit.objects.filter(wallet=wallet).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, wallet: Wallet):
        """
        GIVEN: Wallet model instances in database.
        WHEN: Deposit instance for different Wallets create attempt with name already used in particular Wallet.
        THEN: ValidationError on .full_clean() or IntegrityError on .create() raised.
        """
        payload = self.PAYLOAD.copy()
        payload["wallet"] = wallet
        Deposit.objects.create(**payload)

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            deposit = Deposit(**payload)
            deposit.full_clean()

        assert (
            "Entity with this Name, Wallet and Is deposit already exists."
            in exc.value.error_dict["__all__"][0].messages[0]
        )
        assert Deposit.objects.filter(wallet=wallet).count() == 1

        # .create() scenario
        with pytest.raises(IntegrityError) as exc:
            Deposit.objects.create(**payload)
        assert f'DETAIL:  Key (name, wallet_id, is_deposit)=({payload["name"]}, {wallet.id}, t) already exists.' in str(
            exc.value
        )
        assert Deposit.objects.filter(wallet=wallet).count() == 1
