"""
File containing predefined TransferCategoryGroup and TransferCategory objects that will be created by default
on Budget object creation.

BUDGET_DEFAULTS dictionary contains other dictionaries with:
    * TransferCategoryGroup details.
    * TransferCategories attached to particular TransferCategoryGroup details.
"""
from transfers.models.transfer_category_group_model import TransferCategoryGroup

BUDGET_DEFAULTS = (
    # Expenses
    {
        'group': {
            'name': 'Most important',
            'description': 'Most important needs, like food, clothes, electricity, etc.',
            'transfer_type': TransferCategoryGroup.TransferTypes.EXPENSE,
        },
        'categories': [],
    },
    {
        'group': {
            'name': 'Debts',
            'description': 'Installments, contributions, taxes, etc.',
            'transfer_type': TransferCategoryGroup.TransferTypes.EXPENSE,
        },
        'categories': [],
    },
    {
        'group': {
            'name': 'Reserves and savings',
            'description': 'Reserves, savings, other important expenses.',
            'transfer_type': TransferCategoryGroup.TransferTypes.EXPENSE,
        },
        'categories': [],
    },
    {
        'group': {
            'name': "What's left",
            'description': 'Surpluses, greatest debt, pleasures.',
            'transfer_type': TransferCategoryGroup.TransferTypes.EXPENSE,
        },
        'categories': [],
    },
    # Incomes
    {
        'group': {
            'name': 'Regular income',
            'description': 'Salary, interest, etc.',
            'transfer_type': TransferCategoryGroup.TransferTypes.INCOME,
        },
        'categories': [],
    },
    {
        'group': {
            'name': 'Irregular income',
            'description': 'Sale, gifts, etc.',
            'transfer_type': TransferCategoryGroup.TransferTypes.INCOME,
        },
        'categories': [],
    },
    # Operational
    {
        'group': {
            'name': 'Operational',
            'description': 'For transfers between Budget Deposits.',
            'transfer_type': TransferCategoryGroup.TransferTypes.RELOCATION,
        },
        'categories': [],
    },
)
