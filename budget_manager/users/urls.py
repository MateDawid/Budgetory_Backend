from rest_framework import routers
from users.views import UserViewSet

router = routers.DefaultRouter()
router.register(r'', UserViewSet, basename='user')


urlpatterns = router.urls
