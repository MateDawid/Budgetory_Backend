from budgets.views import BudgetingPeriodViewSet, BudgetViewSet
from rest_framework import routers

app_name = 'budgets'


router = routers.DefaultRouter()
router.register(r'', BudgetViewSet)
router.register(r'periods', BudgetingPeriodViewSet)


urlpatterns = router.urls
