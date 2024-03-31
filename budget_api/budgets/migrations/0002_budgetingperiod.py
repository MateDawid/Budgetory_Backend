# Generated by Django 4.2.3 on 2024-03-23 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BudgetingPeriod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('date_start', models.DateField()),
                ('date_end', models.DateField()),
                ('is_active', models.BooleanField(default=False)),
                ('budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='periods', to='budgets.budget')),
            ],
            options={
                'unique_together': {('name', 'budget')},
            },
        ),
    ]
