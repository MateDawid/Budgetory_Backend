from categories.models.transfer_category_choices import IncomeCategoryPriority
from categories.views.transfer_category_priority_view import TransferCategoryPriorityView


class IncomeCategoryPriorityView(TransferCategoryPriorityView):
    """
    View returning IncomeCategoryPriority choices for IncomeCategory.
    """

    choices = IncomeCategoryPriority.choices
    permission_classes = []
