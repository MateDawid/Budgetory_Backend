from django.urls import path

from categories.views.expense_category_priority_view import ExpenseCategoryPriorityView
from categories.views.income_category_priority_view import IncomeCategoryPriorityView

urlpatterns = [
    path("priorities/expense", ExpenseCategoryPriorityView.as_view(), name="expense-category-priorities"),
    path("priorities/income", IncomeCategoryPriorityView.as_view(), name="income-category-priorities"),
]
