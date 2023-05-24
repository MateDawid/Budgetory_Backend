from data_import import views as data_import_views
from django.urls import include, path
from rest_framework import routers
from users import views as users_views

router = routers.DefaultRouter()
router.register(r'user', users_views.UserViewSet, basename='user')
router.register(r'import_file', data_import_views.ImportFileViewSet, basename='importfile')

urlpatterns = router.urls

urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]
