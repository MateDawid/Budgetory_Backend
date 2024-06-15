from budgets.models import Budget
from rest_framework.viewsets import ModelViewSet


class BudgetModelViewSet(ModelViewSet):
    """ModelViewSet extended with budget property."""

    @property
    def budget(self) -> Budget | None:
        """
        Returns Budget object using budget_pk passes in URL.

        Returns:
            Budget | None: Budget model instance or None.
        """
        budget_pk = self.kwargs.get('budget_pk')
        return Budget.objects.filter(pk=budget_pk).first()
