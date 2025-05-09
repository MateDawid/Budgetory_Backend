# Generated by Django 4.2.19 on 2025-03-21 08:12

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("categories", "0001_initial"),
        ("budgets", "0001_initial"),
        ("entities", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transfer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("description", models.CharField(blank=True, max_length=255, null=True)),
                ("value", models.DecimalField(decimal_places=2, max_digits=10)),
                ("date", models.DateField()),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transfers",
                        to="categories.transfercategory",
                    ),
                ),
                (
                    "deposit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="deposit_transfers",
                        to="entities.deposit",
                    ),
                ),
                (
                    "entity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="entity_transfers",
                        to="entities.entity",
                    ),
                ),
                (
                    "period",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transfers",
                        to="budgets.budgetingperiod",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "transfers",
            },
        ),
        migrations.CreateModel(
            name="Expense",
            fields=[],
            options={
                "verbose_name_plural": "expenses",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("transfers.transfer",),
        ),
        migrations.CreateModel(
            name="Income",
            fields=[],
            options={
                "verbose_name_plural": "incomes",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("transfers.transfer",),
        ),
        migrations.AddConstraint(
            model_name="transfer",
            constraint=models.CheckConstraint(
                check=models.Q(("value__gt", Decimal("0.00"))), name="transfers_transfer_value_gt_0"
            ),
        ),
        migrations.AddConstraint(
            model_name="transfer",
            constraint=models.CheckConstraint(
                check=models.Q(("entity", models.F("deposit")), _negated=True),
                name="transfers_transfer_deposit_and_entity_not_the_same",
            ),
        ),
    ]
