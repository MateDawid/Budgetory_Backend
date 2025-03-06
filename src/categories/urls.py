from django.urls import path

from categories.views.category_priority_view import CategoryPriorityView

app_name = "categories"

urlpatterns = [
    path("priorities", CategoryPriorityView.as_view(), name="category-priorities"),
]
