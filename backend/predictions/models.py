from django.db import models


class ExpensePrediction(models.Model):
    """ExpensePrediction model for planned expenses in particular BudgetingPeriod"""

    period = models.ForeignKey('budgets.BudgetingPeriod', on_delete=models.CASCADE, related_name='expense_predictions')
    category = models.ForeignKey(
        'categories.ExpenseCategory', on_delete=models.CASCADE, related_name='expense_predictions'
    )
    value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('period', 'category')

    def __str__(self) -> str:
        """
        Returns string representation of ExpensePrediction model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f'[{self.period.name}] {self.category.name}'
