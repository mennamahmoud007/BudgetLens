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
    Verifies that the provided input is a valid numerical value greater than zero.
    
    :param amount: The value to be checked.
    :return: True if valid, False otherwise.
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
    Converts a raw numerical value into a human-readable currency string.
    
    :param value: The amount to format.
    :param currency: The currency code (default 'EGP').
    :return: A string formatted with two decimal places and the currency code.
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