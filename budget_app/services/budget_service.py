from decimal import Decimal
from django.utils import timezone
from ..models import BudgetCycle, Expense
from django.db.models import Sum

class BudgetCalculator:
    """
    Service class providing static methods for financial calculations.
    Handles daily limits and budget rollovers.
    """
    @staticmethod
    def calculate_daily_limit(remaining_balance, remaining_days):
        """
        Calculates the maximum recommended spending per day to stay within budget.
        
        :param remaining_balance: The current funds available in the cycle.
        :param remaining_days: Number of days left until the cycle ends.
        :return: Decimal value of the daily limit.
        """
        if remaining_days <= 0:
            return Decimal("0.00")
        return Decimal(remaining_balance) / Decimal(remaining_days)

    @staticmethod
    def apply_daily_rollover(cycle):
        """
        Updates the budget cycle state by calculating total spent and 
        adjusting the daily limit based on the current date.
        """
        today = timezone.now().date()

        effective_end = min(today, cycle.end_date)
        spent = Expense.objects.filter(
            user=cycle.user,
            date__range=(cycle.start_date, effective_end)
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        cycle.remaining_balance = cycle.total_budget - spent
        cycle.last_recalculated_date = today
        cycle.save()
        return cycle


def create_budget_cycle(user, total_budget, start_date=None, end_date=None):
    if start_date is None:
        start_date = timezone.now().date()

    if end_date is None:
        end_date = start_date.replace(day=28) + timezone.timedelta(days=4)
        end_date = end_date - timezone.timedelta(days=end_date.day)

    total_budget = Decimal(str(total_budget))
    total_days = (end_date - start_date).days + 1
    daily_limit = BudgetCalculator.calculate_daily_limit(total_budget, total_days)

    cycle = BudgetCycle.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        total_budget=total_budget,
        remaining_balance=total_budget,
        daily_limit=daily_limit,  
        last_recalculated_date=start_date
    )
    return cycle


def recalculate_daily_limit(cycle):
    cycle = BudgetCalculator.apply_daily_rollover(cycle)
    return cycle.daily_limit


def calculate_daily_average(cycle):
    cycle = BudgetCalculator.apply_daily_rollover(cycle)
    today = timezone.now().date()
    remaining_days = (cycle.end_date - today).days + 1

    if remaining_days <= 0:
        return cycle.remaining_balance

    return cycle.remaining_balance / remaining_days


def reset_budget_cycle(user):
    cycle = BudgetCycle.objects.filter(user=user).last()
    if cycle:
        cycle.delete()