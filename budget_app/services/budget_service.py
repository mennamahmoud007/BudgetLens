from django.utils import timezone
from ..models import BudgetCycle

def create_budget_cycle(user, total_budget, start_date=None, end_date=None):
    if start_date is None:
        start_date = timezone.now().date()
    if end_date is None:
        # Default to end of month
        end_date = start_date.replace(day=28) + timezone.timedelta(days=4)  
        end_date = end_date - timezone.timedelta(days=end_date.day)
    
    cycle = BudgetCycle.objects.create(
        user=user,
        start_date=start_date,
        end_date=end_date,
        total_budget=total_budget
    )
    return cycle

def recalculate_daily_limit(cycle):

    from datetime import timedelta
    total_days = (cycle.end_date - cycle.start_date).days + 1
    daily_limit = cycle.total_budget / total_days
    return daily_limit

def calculate_daily_average(cycle):
    today = timezone.now().date()
    remaining_days = (cycle.end_date - today).days + 1
    
    if remaining_days <= 0:
        return cycle.remaining_budget
    
    daily_average = cycle.remaining_budget / remaining_days
    return daily_average
from ..models import BudgetCycle

def reset_budget_cycle(user):
    cycle = BudgetCycle.objects.filter(user=user).last()
    
    if cycle:
        cycle.delete()  