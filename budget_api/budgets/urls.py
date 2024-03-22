from budgets.views import BudgetViewSet
from rest_framework import routers

app_name = 'budgets'


router = routers.DefaultRouter()
router.register(r'', BudgetViewSet)
# router.register(r'', BudgetingPeriodViewSet)


urlpatterns = router.urls
