from django.contrib import admin
from transfers.models.transfer_category_group_model import TransferCategoryGroup
from transfers.models.transfer_category_model import TransferCategory

admin.site.register(TransferCategoryGroup)
admin.site.register(TransferCategory)
