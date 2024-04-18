from rest_framework import routers
from transfers.views.transfer_category_view import TransferCategoryViewSet

app_name = 'transfers'

router = routers.DefaultRouter()
router.register(r'categories', TransferCategoryViewSet)


urlpatterns = router.urls
