from entities.views import EntityViewSet
from rest_framework import routers

app_name = 'entities'

router = routers.DefaultRouter()
router.register(r'', EntityViewSet)


urlpatterns = router.urls
