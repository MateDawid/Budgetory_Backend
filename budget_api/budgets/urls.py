from budgets.views import BudgetingPeriodViewSet
from rest_framework import routers

app_name = 'budgets'

router = routers.DefaultRouter()
router.register(r'', BudgetingPeriodViewSet)


urlpatterns = router.urls
