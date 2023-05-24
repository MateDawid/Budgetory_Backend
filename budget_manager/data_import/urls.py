from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('data_import', TemplateView.as_view(template_name='data_import.html'), name='data_import'),
]
