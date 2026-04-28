# Alert Service
from decimal import Decimal

def check_threshold(spent, total_budget):
    spent_decimal = Decimal(str(spent))
    threshold = Decimal('0.8') * total_budget
    return spent_decimal >= threshold

def trigger_alert():
    return "Warning: You reached 80% of your budget!"