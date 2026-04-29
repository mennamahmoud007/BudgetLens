"""
Utility functions for the budget app for validation, formatting, etc.
"""

from datetime import datetime, date
from typing import Optional



DATE_FORMAT = "%Y-%m-%d"


# -----------------------------
# Validation Functions
# -----------------------------
def validate_amount(amount: any) -> bool:
    """
    Check if amount is a valid positive number.
    """
    try:
        value = float(amount)
        return value > 0
    except (ValueError, TypeError):
        return False


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Ensure end date is after start date.
    """
    if not start_date or not end_date:
        return False
    return end_date > start_date


def is_valid_category(category: any) -> bool:
    """
    Validate expense category.
    """
    return isinstance(category, str) and category.strip() != ""


# -----------------------------
# Formatting Functions
# -----------------------------
def format_currency(value: any, currency: str = "EGP") -> str:
    """
    Format a number into currency format.
    """
    try:
        return f"{float(value):,.2f} {currency}"
    except (ValueError, TypeError):
        return f"0.00 {currency}"


# -----------------------------
# Date Helpers
# -----------------------------
def parse_date(date_str: str) -> Optional[date]:
    """
    Convert string to date object safely.
    """
    try:
        return datetime.strptime(date_str, DATE_FORMAT).date()
    except (ValueError, TypeError):
        return None


def today_date() -> date:
    """
    Return today's date.
    """
    return date.today()