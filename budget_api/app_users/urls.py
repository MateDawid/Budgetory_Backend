from app_users.views import UserViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', UserViewSet, basename='user')


urlpatterns = router.urls
