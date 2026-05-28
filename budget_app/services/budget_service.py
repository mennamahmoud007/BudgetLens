from decimal import Decimal
from django.utils import timezone
from ..models import BudgetCycle, Expense
from django.db.models import Sum


class BudgetCalculator:

    @staticmethod
    def calculate_daily_limit(remaining_balance, remaining_days):
        if remaining_days <= 0:
            return Decimal("0.00")
        return Decimal(str(remaining_balance)) / Decimal(str(remaining_days))

    @staticmethod
    def apply_daily_rollover(cycle):
        today = timezone.now().date()
        effective_end = min(today, cycle.end_date)
        spent = Expense.objects.filter(
            user=cycle.user,
            date__range=(cycle.start_date, effective_end)
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        spent = Decimal(str(spent))
        remaining = cycle.total_budget - spent
        remaining_days = (cycle.end_date - today).days + 1

        cycle.remaining_balance = remaining
        cycle.daily_limit = BudgetCalculator.calculate_daily_limit(remaining, remaining_days)
        cycle.last_recalculated_date = today
        cycle.save(update_fields=["remaining_balance", "daily_limit", "last_recalculated_date"])
        return cycle


def create_budget_cycle(user, total_budget, start_date=None, end_date=None):
    BudgetCycle.objects.filter(user=user).delete()

    if start_date is None:
        start_date = timezone.now().date()
    if end_date is None:
        next_month = start_date.replace(day=28) + timezone.timedelta(days=4)
        end_date = next_month - timezone.timedelta(days=next_month.day)

    total_budget = Decimal(str(total_budget))
    total_days = (end_date - start_date).days + 1
    daily_limit = BudgetCalculator.calculate_daily_limit(total_budget, total_days)

    return BudgetCycle.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        total_budget=total_budget,
        remaining_balance=total_budget,
        daily_limit=daily_limit,
        last_recalculated_date=start_date,
    )


def recalculate_daily_limit(cycle):
    updated = BudgetCalculator.apply_daily_rollover(cycle)
    return updated.daily_limit


def calculate_daily_average(cycle):
    today = timezone.now().date()
    remaining_days = (cycle.end_date - today).days + 1
    if remaining_days <= 0:
        return cycle.remaining_balance
    return cycle.remaining_balance / Decimal(str(remaining_days))


def reset_budget_cycle(user):
    BudgetCycle.objects.filter(user=user).delete()
    Expense.objects.filter(user=user).delete()