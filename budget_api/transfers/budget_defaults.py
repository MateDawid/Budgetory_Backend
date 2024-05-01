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
        'categories': [
            {
                'name': 'Flat fee',
                'description': 'Expenses for flat fee.',
            },
            {
                'name': 'Food',
                'description': 'Expenses for food.',
            },
        ],
    },
    {
        'group': {
            'name': 'Debts',
            'description': 'Installments, contributions, taxes, etc.',
            'transfer_type': TransferCategoryGroup.TransferTypes.EXPENSE,
        },
        'categories': [
            {
                'name': 'Taxes',
                'description': 'Expenses for taxes.',
            },
            {
                'name': 'Installments',
                'description': 'Expenses for installments.',
            },
        ],
    },
    {
        'group': {
            'name': 'Reserves and savings',
            'description': 'Reserves, savings, other important expenses.',
            'transfer_type': TransferCategoryGroup.TransferTypes.EXPENSE,
        },
        'categories': [
            {
                'name': 'Reserves',
                'description': 'Money saved for reserves.',
            },
            {
                'name': 'Important expenses',
                'description': 'Other important expenses.',
            },
        ],
    },
    {
        'group': {
            'name': "What's left",
            'description': 'Surpluses, greatest debt, pleasures.',
            'transfer_type': TransferCategoryGroup.TransferTypes.EXPENSE,
        },
        'categories': [
            {
                'name': 'Greatest debt',
                'description': 'Expense for greatest debt.',
            },
            {
                'name': 'Entertainment',
                'description': 'Expenses for entertainment.',
            },
        ],
    },
    # Incomes
    {
        'group': {
            'name': 'Regular income',
            'description': 'Salary, interest, etc.',
            'transfer_type': TransferCategoryGroup.TransferTypes.INCOME,
        },
        'categories': [
            {
                'name': 'Salary',
                'description': 'Monthly salary.',
            },
            {
                'name': 'Interest',
                'description': 'Monthly interests.',
            },
        ],
    },
    {
        'group': {
            'name': 'Irregular income',
            'description': 'Sale, gifts, etc.',
            'transfer_type': TransferCategoryGroup.TransferTypes.INCOME,
        },
        'categories': [
            {
                'name': 'Gifts',
                'description': 'Money got as gift.',
            },
            {
                'name': 'Sale',
                'description': 'Money earned from selling stuff.',
            },
        ],
    },
    # Operational
    {
        'group': {
            'name': 'Operational',
            'description': 'For transfers between Budget Deposits.',
            'transfer_type': TransferCategoryGroup.TransferTypes.RELOCATION,
        },
        'categories': [
            {
                'name': 'Payment of reserves',
                'description': 'Moving money from Reserve Deposit to other one.',
            },
            {
                'name': 'Transfer between accounts',
                'description': 'Moving money from one Deposit to other one.',
            },
        ],
    },
)
