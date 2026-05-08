# Alert Service
from decimal import Decimal

def check_threshold(spent, total_budget):
    """
    Determines if a user has reached the 80% spending threshold.
    
    :param spent: Total amount spent in the current cycle.
    :param total_budget: The total limit set for the cycle.
    :return: Boolean (True if 80% or more is spent).
    """
    spent_decimal = Decimal(str(spent))
    threshold = Decimal('0.8') * total_budget
    return spent_decimal >= threshold

def trigger_alert():
    """
    Returns a warning message string when a budget threshold is breached.
    """
    return "Warning: You reached 80% of your budget!"
