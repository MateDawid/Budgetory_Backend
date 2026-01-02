from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("budgets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BudgetingPeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.PositiveSmallIntegerField(choices=[(1, "📝 Draft"), (2, "🟢 Active"), (3, "🔒 Closed")]),
                ),
                ("name", models.CharField(max_length=128)),
                ("date_start", models.DateField()),
                ("date_end", models.DateField()),
                (
                    "budget",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="periods", to="budgets.budget"
                    ),
                ),
                ("previous_period",
                 models.ForeignKey(
                     blank=True,
                     help_text="Reference to the previous budgeting period within the same budget",
                     null=True,
                     on_delete=django.db.models.deletion.SET_NULL,
                     related_name="next_periods",
                     to="periods.budgetingperiod",
                 )),
            ],
            options={
                "unique_together": {("name", "budget")},
            },
        ),
    ]
