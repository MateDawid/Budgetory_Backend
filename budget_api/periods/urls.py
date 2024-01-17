from periods.views import BudgetingPeriodViewSet
from rest_framework import routers

app_name = 'periods'

router = routers.DefaultRouter()
router.register(r'', BudgetingPeriodViewSet)


urlpatterns = router.urls
