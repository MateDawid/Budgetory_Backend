from django.urls import path

from categories.views.category_priority_view import CategoryPriorityView
from categories.views.category_type_view import CategoryTypeView

app_name = "categories"

urlpatterns = [
    path("priorities", CategoryPriorityView.as_view(), name="category-priority"),
    path("types", CategoryTypeView.as_view(), name="category-type"),
]
