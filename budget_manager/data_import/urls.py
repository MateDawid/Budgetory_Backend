from data_import.views import ImportFileViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', ImportFileViewSet, basename='importfile')


urlpatterns = router.urls
