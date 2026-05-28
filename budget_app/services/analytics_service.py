from django.db.models import Sum
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from abc import ABC, abstractmethod


class ChartStrategy(ABC):
    @abstractmethod
    def format_data(self, category_data):
        pass


class PieChartStrategy(ChartStrategy):
    def format_data(self, category_data):
        return {
            'type': 'pie',
            'labels': list(category_data.keys()),
            'values': list(category_data.values()),
            'options': {'responsive': True}
        }


class BarChartStrategy(ChartStrategy):
    def format_data(self, category_data):
        return {
            'type': 'bar',
            'labels': list(category_data.keys()),
            'values': list(category_data.values()),
            'options': {'barPercentage': 0.8}
        }


class LineChartStrategy(ChartStrategy):
    def format_data(self, category_data):
        return {
            'type': 'line',
            'labels': list(category_data.keys()),
            'values': list(category_data.values()),
            'options': {'trend': 'smooth'}
        }


def _safe_amount(expense):
    try:
        val = expense.amount
        if val is None:
            return 0.0
        return float(Decimal(str(val)))
    except (InvalidOperation, ValueError, TypeError):
        return 0.0


class AnalyticsService:

    def __init__(self, strategy=None):
        self._strategy = strategy or PieChartStrategy()

    def set_strategy(self, strategy):
        self._strategy = strategy

    def get_chart_data(self, data):
        return self._strategy.format_data(data)

    @staticmethod
    def get_spending_by_category(user, days=30):
        start_date = datetime.now().date() - timedelta(days=days)
        expenses = user.expense_set.filter(date__gte=start_date).select_related('category')
        category_totals = defaultdict(float)
        for expense in expenses:
            try:
                cat_name = expense.category.name if expense.category else "Uncategorized"
                category_totals[cat_name] += _safe_amount(expense)
            except Exception:
                continue
        return dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def get_monthly_trend(user, months=6):
        start_date = datetime.now().date() - timedelta(days=months * 30)
        expenses = user.expense_set.filter(date__gte=start_date)
        monthly_data = defaultdict(float)
        for expense in expenses:
            try:
                month_key = expense.date.strftime("%b %Y")
                monthly_data[month_key] += _safe_amount(expense)
            except Exception:
                continue
        return dict(monthly_data)

    @staticmethod
    def get_top_categories(user, limit=5, days=30):
        start_date = datetime.now().date() - timedelta(days=days)
        expenses = user.expense_set.filter(date__gte=start_date).select_related('category')
        category_totals = defaultdict(float)
        for expense in expenses:
            try:
                cat_name = expense.category.name if expense.category else "Uncategorized"
                category_totals[cat_name] += _safe_amount(expense)
            except Exception:
                continue
        result = [{'category': cat, 'total': total} for cat, total in category_totals.items()]
        result.sort(key=lambda x: x['total'], reverse=True)
        return result[:limit]

    @staticmethod
    def get_total_spending(user, days=30):
        start_date = datetime.now().date() - timedelta(days=days)
        total = user.expense_set.filter(date__gte=start_date).aggregate(total=Sum('amount'))['total']
        if total is None:
            return 0.0
        try:
            return float(Decimal(str(total)))
        except (InvalidOperation, ValueError):
            return 0.0

    @staticmethod
    def get_daily_average(user, days=30):
        total = AnalyticsService.get_total_spending(user, days)
        return total / days if days > 0 else 0.0

    @staticmethod
    def get_weekly_comparison(user):
        today = datetime.now().date()
        this_week_start = today - timedelta(days=today.weekday())
        last_week_start = this_week_start - timedelta(days=7)

        def safe_total(qs):
            val = qs.aggregate(total=Sum('amount'))['total']
            if val is None:
                return 0.0
            try:
                return float(Decimal(str(val)))
            except (InvalidOperation, ValueError):
                return 0.0

        this_week = safe_total(user.expense_set.filter(date__gte=this_week_start))
        last_week = safe_total(user.expense_set.filter(
            date__gte=last_week_start,
            date__lt=this_week_start
        ))
        percent_change = 0.0
        if last_week > 0:
            percent_change = ((this_week - last_week) / last_week) * 100
        return {
            'this_week': this_week,
            'last_week': last_week,
            'percent_change': round(percent_change, 1),
        }