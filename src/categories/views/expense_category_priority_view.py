from categories.models.transfer_category_choices import ExpenseCategoryPriority
from categories.views.transfer_category_priority_view import TransferCategoryPriorityView


class ExpenseCategoryPriorityView(TransferCategoryPriorityView):
    """
    View returning ExpenseCategoryPriority choices for ExpenseCategory.
    """

    choices = ExpenseCategoryPriority.choices
    permission_classes = []
