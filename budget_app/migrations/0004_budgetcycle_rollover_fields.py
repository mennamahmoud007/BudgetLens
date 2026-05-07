# Generated manually for BudgetCycle rollover fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget_app', '0003_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetcycle',
            name='remaining_balance',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='budgetcycle',
            name='daily_limit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='budgetcycle',
            name='last_recalculated_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
