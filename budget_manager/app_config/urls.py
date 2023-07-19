from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers

router = routers.SimpleRouter()

front_urls = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('data_import/', TemplateView.as_view(template_name='data_import.html'), name='data_import'),
]

urlpatterns = [
    path('', include(front_urls)),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
    path('api/users/', include('users.urls')),
    path('api/data_import/', include('data_import.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
