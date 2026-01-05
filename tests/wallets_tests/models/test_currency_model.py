import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from wallets.models.currency_model import Currency


@pytest.mark.django_db
class TestCurrencyModel:
    """Tests for Currency model"""

    @pytest.mark.parametrize("name", ["NPR", "xCd", "xpf"])
    def test_create_object(self, name: str):
        """
        GIVEN: Valid currency name.
        WHEN: Currency instance create attempt with valid data.
        THEN: Currency model instance exists in database with name in uppercase.
        """
        currency = Currency.objects.create(name=name)
        upper_name = name.upper()
        assert Currency.objects.filter(name=upper_name).exists()
        assert str(currency) == currency.name
        assert currency.name == upper_name

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self):
        """
        GIVEN: Too long currency name.
        WHEN: Currency instance create attempt with name too long.
        THEN: DataError raised. Object not created in database.
        """
        name = "NPRX"
        with pytest.raises(IntegrityError) as exc:
            Currency.objects.create(name=name)
        assert 'new row for relation "wallets_currency" violates check constraint "currency_name_len_exact_3"' in str(
            exc.value
        )
        assert not Currency.objects.filter(name=name).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_short(self):
        """
        GIVEN: Too short currency name.
        WHEN: Currency instance create attempt with name too short.
        THEN: DataError raised. Object not created in database.
        """
        name = "NP"
        with pytest.raises(IntegrityError) as exc:
            Currency.objects.create(name=name)
        assert 'new row for relation "wallets_currency" violates check constraint "currency_name_len_exact_3"' in str(
            exc.value
        )
        assert not Currency.objects.filter(name=name).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_currency_exists_already(self):
        """
        GIVEN: Currency object existing in database.
        WHEN: Currency instance create attempt with valid data, but with already used name.
        THEN: Object not created in database.
        """
        name = "NPR"
        Currency.objects.create(name=name)
        assert Currency.objects.filter(name=name).count() == 1

        # .full_clean() & .save() scenario
        with pytest.raises(ValidationError) as exc:
            currency = Currency(name=name)
            currency.full_clean()

        assert "Currency with this Name already exists." in exc.value.error_dict["name"][0].messages[0]
        assert Currency.objects.filter(name=name).count() == 1

        # .create() scenario
        with pytest.raises(IntegrityError) as exc:
            Currency.objects.create(name=name)
        assert f"DETAIL:  Key (name)=({name.upper()}) already exists." in str(exc.value)
        assert Currency.objects.filter(name=name).count() == 1
