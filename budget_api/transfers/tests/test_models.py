# import pytest
# from django.db import DataError
# from factory.base import FactoryMetaClass
# from transfers.models import TransferCategory
#
#
# @pytest.mark.django_db
# class TestTransferCategoryModel:
#     """Tests for TransferCategory model"""
#
#     PAYLOAD = {'name': 'Food', 'description': 'Category for food expenses.', 'is_active': True}
#
#     def test_create_category_without_owner(self, transfer_category_group: TransferCategoryGroup):
#         """
#         GIVEN: TransferCategoryGroup model instance for Budget in database. Valid payload for TransferCategory
#         without owner provided.
#         WHEN: TransferCategory instance create attempt with valid data.
#         THEN: TransferCategory model instance exists in database with given data.
#         """
#         category = TransferCategory.objects.create(group=transfer_category_group, **self.PAYLOAD)
#
#         for key in self.PAYLOAD:
#             assert getattr(category, key) == self.PAYLOAD[key]
#         assert category.owner is None
#         assert TransferCategory.objects.filter(group=transfer_category_group).count() == 1
#         assert str(category) == f'{category.name} ({category.group.name})'
#
#     def test_create_category_with_owner(
#         self, user_factory: FactoryMetaClass, transfer_category_group: TransferCategoryGroup
#     ):
#         """
#         GIVEN: TransferCategoryGroup model instance for Budget in database. Valid payload for TransferCategory
#         with owner provided.
#         WHEN: TransferCategory instance create attempt with valid data.
#         THEN: TransferCategory model instance exists in database with given data.
#         """
#         payload = self.PAYLOAD.copy()
#         category_owner = user_factory()
#         transfer_category_group.budget.members.add(category_owner)
#         payload['owner'] = category_owner
#
#         category = TransferCategory.objects.create(group=transfer_category_group, **payload)
#
#         for key in payload:
#             if key == 'owner':
#                 continue
#             assert getattr(category, key) == self.PAYLOAD[key]
#         assert category.owner == category_owner
#         assert TransferCategory.objects.filter(group=transfer_category_group).count() == 1
#         assert str(category) == f'{category.name} ({category.group.name})'
#
#     def test_creating_same_category_for_two_groups(self, transfer_category_group_factory: FactoryMetaClass):
#         """
#         GIVEN: Two TransferCategoryGroup model instances for Budget in database.
#         WHEN: Same TransferCategory instance for different TransferCategoryGroups create attempt with valid data.
#         THEN: Two TransferCategory model instances existing in database with given data.
#         """
#         group_1 = transfer_category_group_factory()
#         group_2 = transfer_category_group_factory()
#         payload = self.PAYLOAD.copy()
#         for group in (group_1, group_2):
#             payload['group'] = group
#             TransferCategory.objects.create(**payload)
#
#         assert TransferCategory.objects.all().count() == 2
#         assert TransferCategory.objects.filter(group=group).count() == 1
#         assert TransferCategory.objects.filter(group=group).count() == 1
#
#     @pytest.mark.django_db(transaction=True)
#     @pytest.mark.parametrize('field_name', ['name', 'description'])
#     def test_error_value_too_long(self, transfer_category_group: TransferCategoryGroup, field_name: str):
#         """
#         GIVEN: TransferCategoryGroup model instance in database.
#         WHEN: TransferCategory instance create attempt with field value too long.
#         THEN: DataError raised.
#         """
#         max_length = TransferCategory._meta.get_field(field_name).max_length
#         payload = self.PAYLOAD.copy()
#         payload[field_name] = (max_length + 1) * 'a'
#
#         with pytest.raises(DataError) as exc:
#             TransferCategory.objects.create(**payload)
#         assert str(exc.value) == f'value too long for type character varying({max_length})\n'
#         assert not TransferCategory.objects.filter(group=transfer_category_group).exists()
