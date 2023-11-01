from periods.views import BudgetingPeriodViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', BudgetingPeriodViewSet)


urlpatterns = router.urls
