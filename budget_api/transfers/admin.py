from django.contrib import admin
from transfers.models.transfer_category import TransferCategory
from transfers.models.transfer_category_group import TransferCategoryGroup

admin.site.register(TransferCategoryGroup)
admin.site.register(TransferCategory)
