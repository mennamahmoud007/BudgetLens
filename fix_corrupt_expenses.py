"""
fix_corrupt_expenses.py
========================
Run this ONCE from your project root to clean up any corrupt expense records
that are causing the decimal.InvalidOperation crash:

    python fix_corrupt_expenses.py

It will set any invalid/null amounts to 0.01 so Django can read them,
then print a report of how many were fixed.
"""

import os
import sys
import django

# ---- Bootstrap Django ----
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budgetlens.settings')

# Make sure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

# ---- Now safe to import models ----
from decimal import Decimal, InvalidOperation
from budget_app.models import Expense, BudgetCycle
from django.db import connection

fixed = 0
skipped = 0

print("Scanning expenses for corrupt decimal values...")

# We read raw values directly from the DB to bypass Django's converter
with connection.cursor() as cursor:
    cursor.execute("SELECT id, amount FROM budget_app_expense")
    rows = cursor.fetchall()

for row_id, raw_amount in rows:
    bad = False
    if raw_amount is None or str(raw_amount).strip() == '':
        bad = True
    else:
        try:
            Decimal(str(raw_amount))
        except (InvalidOperation, ValueError):
            bad = True

    if bad:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE budget_app_expense SET amount = '0.01' WHERE id = %s",
                [row_id]
            )
        print(f"  Fixed expense id={row_id} (was: {repr(raw_amount)})")
        fixed += 1
    else:
        skipped += 1

print(f"\nDone. Fixed: {fixed}  |  Already OK: {skipped}")

# ---- Recalculate all budget cycles ----
if fixed > 0:
    print("\nRecalculating all budget cycles...")
    from budget_app.services.budget_service import BudgetCalculator
    for cycle in BudgetCycle.objects.all():
        BudgetCalculator.apply_daily_rollover(cycle)
        print(f"  Recalculated cycle id={cycle.id} for user={cycle.user}")

print("\nAll done! You can now start the server normally.")