from app_users import views
from django.urls import path

app_name = 'app_users'

urlpatterns = [
    path('', views.ListUserView.as_view(), name='list'),
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('me/', views.AuthenticatedUserView.as_view(), name='me'),
]
