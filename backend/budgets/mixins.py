from budgets.models import Budget
from rest_framework.request import Request


class BudgetMixin:
    """Mixin retrieving Budget instance in ViewSet with /budgets root"""

    def initialize_request(self, request: Request, *args, **kwargs) -> Request:
        """
        Extends ViewSetMixin.initializer_request method with Budget instance from URL.

        Args:
            request [Request]: User request.

        Returns:
            Request: Request object extended with budget param.
        """
        request = super().initialize_request(request, *args, **kwargs)
        budget_pk = request.parser_context.get('kwargs', {}).get('budget_pk')
        budget = Budget.objects.filter(pk=budget_pk).first()
        setattr(request, 'budget', budget)
        return request
