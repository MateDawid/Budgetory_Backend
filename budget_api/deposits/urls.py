from deposits.views import DepositViewSet
from rest_framework import routers

app_name = 'deposits'

router = routers.DefaultRouter()
router.register(r'', DepositViewSet)


urlpatterns = router.urls
