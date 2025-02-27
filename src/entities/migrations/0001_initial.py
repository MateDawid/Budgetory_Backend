# Generated by Django 4.2.19 on 2025-02-27 06:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("budgets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Entity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("is_deposit", models.BooleanField(default=False)),
                (
                    "budget",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="entities", to="budgets.budget"
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "entities",
                "unique_together": {("name", "budget")},
            },
        ),
        migrations.CreateModel(
            name="Deposit",
            fields=[],
            options={
                "verbose_name_plural": "deposits",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("entities.entity",),
        ),
    ]
