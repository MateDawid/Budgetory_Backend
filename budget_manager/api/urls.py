from django.urls import path, include
from users import views as users_views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'user', users_views.UserViewSet, basename='user')

urlpatterns = router.urls

urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]
