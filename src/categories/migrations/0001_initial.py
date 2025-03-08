# Generated by Django 4.2.19 on 2025-03-07 06:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("budgets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="TransferCategory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("description", models.CharField(blank=True, max_length=255, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("category_type", models.PositiveSmallIntegerField(choices=[(1, "📈 Income"), (2, "📉 Expense")])),
                (
                    "priority",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "📈 01. Regular"),
                            (2, "📈 02. Irregular"),
                            (3, "📉 01. Most important"),
                            (4, "📉 02. Debts"),
                            (5, "📉 03. Savings"),
                            (6, "📉 04. Others"),
                        ]
                    ),
                ),
                (
                    "budget",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transfer_categories",
                        to="budgets.budget",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_transfer_categories",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "transfer categories",
            },
        ),
        migrations.AddConstraint(
            model_name="transfercategory",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("category_type", 1), ("priority__in", (1, 2))),
                    models.Q(("category_type", 2), ("priority__in", (3, 4, 5, 6))),
                    _connector="OR",
                ),
                name="categories_transfercategory_correct_priority_for_type",
            ),
        ),
        migrations.AddConstraint(
            model_name="transfercategory",
            constraint=models.UniqueConstraint(
                condition=models.Q(("owner__isnull", False)),
                fields=("budget", "category_type", "name", "owner"),
                name="categories_transfercategory_name_unique_for_owner",
            ),
        ),
        migrations.AddConstraint(
            model_name="transfercategory",
            constraint=models.UniqueConstraint(
                condition=models.Q(("owner__isnull", True)),
                fields=("budget", "category_type", "name"),
                name="categories_transfercategory_name_unique_when_no_owner",
            ),
        ),
    ]
