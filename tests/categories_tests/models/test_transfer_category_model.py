import pytest
from categories_tests.utils import INVALID_TYPE_AND_PRIORITY_COMBINATIONS, VALID_TYPE_AND_PRIORITY_COMBINATIONS
from django.db import DataError, IntegrityError
from factory.base import FactoryMetaClass

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from categories.models.transfer_category_model import TransferCategory
from wallets.models.wallet_model import Wallet


@pytest.mark.django_db
class TestTransferCategoryModel:
    """Tests for TransferCategory model"""

    PAYLOAD = {
        "name": "Category name",
        "description": "Category description.",
        "is_active": True,
        "category_type": CategoryType.EXPENSE,
        "priority": CategoryPriority.MOST_IMPORTANT,
    }

    @pytest.mark.parametrize("category_type, priority", VALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_create_transfer_category(
        self, wallet: Wallet, category_type: CategoryType, priority: CategoryPriority, deposit_factory: FactoryMetaClass
    ):
        """
        GIVEN: wallet model instance in database. Valid payload for TransferCategory.
        WHEN: TransferCategory instance create attempt with valid data.
        THEN: TransferCategory model instance created in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority
        payload["deposit"] = deposit_factory(wallet=wallet)

        category = TransferCategory.objects.create(wallet=wallet, **payload)

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert TransferCategory.objects.filter(wallet=wallet).count() == 1
        assert str(category) == f"({category_type.label}) {category.name}"

    @pytest.mark.parametrize("category_type, priority", VALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_save_transfer_category(
        self, wallet: Wallet, category_type: CategoryType, priority: CategoryPriority, deposit_factory: FactoryMetaClass
    ):
        """
        GIVEN: wallet model instance in database.
        WHEN: TransferCategory instance save attempt with valid data.
        THEN: TransferCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority
        payload["deposit"] = deposit_factory(wallet=wallet)

        category = TransferCategory(wallet=wallet, **payload)
        category.full_clean()
        category.save()
        category.refresh_from_db()

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert TransferCategory.objects.filter(wallet=wallet).count() == 1
        assert str(category) == f"({category_type.label}) {category.name}"

    def test_creating_same_category_for_two_wallets(
        self, wallet_factory: FactoryMetaClass, deposit_factory: FactoryMetaClass
    ):
        """
        GIVEN: Two wallet model instances in database.
        WHEN: Same TransferCategory instance for different wallets create attempt with valid data.
        THEN: Two TransferCategory model instances existing in database with given data.
        """
        wallet_1 = wallet_factory()
        wallet_2 = wallet_factory()
        payload = self.PAYLOAD.copy()

        for wallet in (wallet_1, wallet_2):
            payload["wallet"] = wallet
            payload["deposit"] = deposit_factory(wallet=wallet)
            TransferCategory.objects.create(**payload)

        assert TransferCategory.objects.all().count() == 2
        assert TransferCategory.objects.filter(wallet=wallet_1).count() == 1
        assert TransferCategory.objects.filter(wallet=wallet_2).count() == 1

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(self, wallet: Wallet, field_name: str):
        """
        GIVEN: wallet model instance in database.
        WHEN: TransferCategory instance create attempt with field value too long.
        THEN: DataError raised.
        """
        max_length = TransferCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        with pytest.raises(DataError) as exc:
            TransferCategory.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not TransferCategory.objects.filter(wallet=wallet).exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("category_type, priority", INVALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_error_invalid_priority_for_category_type(
        self,
        wallet: Wallet,
        deposit_factory: FactoryMetaClass,
        category_type: CategoryType,
        priority: CategoryPriority,
    ):
        """
        GIVEN: wallet model instance in database.
        WHEN: TransferCategory instance create attempt with invalid priority for category_type.
        THEN: IntegrityError raised. TransferCategory not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["priority"] = priority
        payload["category_type"] = category_type
        payload["deposit"] = deposit_factory(wallet=wallet)

        with pytest.raises(IntegrityError) as exc:
            TransferCategory.objects.create(wallet=wallet, **payload)

        assert (
            'new row for relation "categories_transfercategory" violates check constraint '
            '"categories_transfercategory_correct_priority_for_type"' in str(exc.value)
        )
        assert not TransferCategory.objects.filter(wallet=wallet).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_not_unique_category(
        self, wallet: Wallet, deposit_factory: FactoryMetaClass, transfer_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: TransferCategory model instance created in database.
        WHEN: TransferCategory instance create attempt violating unique constraint.
        THEN: IntegrityError raised. TransferCategory not created in database.
        """
        payload: dict = self.PAYLOAD.copy()
        payload["wallet"] = wallet
        payload["deposit"] = deposit_factory(wallet=wallet)
        transfer_category_factory(**payload)

        with pytest.raises(IntegrityError) as exc:
            TransferCategory.objects.create(**payload)

        assert (
            'duplicate key value violates unique constraint "categories_transfercategory_name_unique_for_deposit"'
            in str(exc.value)
        )
        assert TransferCategory.objects.filter(wallet=wallet).count() == 1
