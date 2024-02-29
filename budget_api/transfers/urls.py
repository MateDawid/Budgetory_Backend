from rest_framework import routers
from transfers.views import TransferCategoryViewSet

app_name = 'transfers'

router = routers.DefaultRouter()
router.register(r'categories', TransferCategoryViewSet)


urlpatterns = router.urls
