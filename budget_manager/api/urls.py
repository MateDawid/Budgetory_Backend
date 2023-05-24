from django.urls import include, path
from rest_framework import routers
from users import views as users_views

router = routers.DefaultRouter()
router.register(r'user', users_views.UserViewSet, basename='user')

urlpatterns = router.urls

urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]
