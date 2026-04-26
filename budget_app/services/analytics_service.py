# Analytics Service
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

class AnalyticsService:
    """Business logic for insights and analytics"""
    
    @staticmethod
    def get_spending_by_category(user, days=30):
        """
        Get spending grouped by category for last N days
        Returns: dict {category_name: total_amount}
        """
        start_date = datetime.now().date() - timedelta(days=days)
        expenses = user.expense_set.filter(date__gte=start_date)
        
        # Group by category name
        category_totals = defaultdict(float)
        for expense in expenses:
            cat_name = expense.category.name if expense.category else "Uncategorized"
            category_totals[cat_name] += float(expense.amount)
        
        # Sort by amount (highest first)
        sorted_totals = dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_totals
    
    @staticmethod
    def get_monthly_trend(user, months=6):
        """
        Get spending trend month by month
        Returns: dict {month_name: total_amount}
        """
        start_date = datetime.now().date() - timedelta(days=months*30)
        expenses = user.expense_set.filter(date__gte=start_date)
        
        # Group by month
        monthly_data = defaultdict(float)
        for expense in expenses:
            month_key = expense.date.strftime("%B %Y")  # e.g., "January 2024"
            monthly_data[month_key] += float(expense.amount)
        
        return dict(monthly_data)
    
    @staticmethod
    def get_top_categories(user, limit=5, days=30):
        """
        Get top spending categories
        Returns: list of dicts with category and total
        """
        start_date = datetime.now().date() - timedelta(days=days)
        expenses = user.expense_set.filter(date__gte=start_date)
        
        # Aggregate by category
        category_totals = defaultdict(float)
        for expense in expenses:
            cat_name = expense.category.name if expense.category else "Uncategorized"
            category_totals[cat_name] += float(expense.amount)
        
        # Convert to list of dicts and sort
        result = [
            {'category': cat, 'total': total}
            for cat, total in category_totals.items()
        ]
        result.sort(key=lambda x: x['total'], reverse=True)
        
        return result[:limit]
    
    @staticmethod
    def get_total_spending(user, days=30):
        """Get total spending for a period"""
        start_date = datetime.now().date() - timedelta(days=days)
        total = user.expense_set.filter(date__gte=start_date).aggregate(
            total=Sum('amount')
        )['total']
        return float(total) if total else 0.0
    
    @staticmethod
    def get_daily_average(user, days=30):
        """Get average spending per day"""
        total = AnalyticsService.get_total_spending(user, days)
        return total / days if days > 0 else 0
    
    @staticmethod
    def get_spending_summary(user, days=30):
        """
        Get complete spending summary
        Returns: dict with all analytics
        """
        return {
            'total_spent': AnalyticsService.get_total_spending(user, days),
            'daily_average': AnalyticsService.get_daily_average(user, days),
            'by_category': AnalyticsService.get_spending_by_category(user, days),
            'top_categories': AnalyticsService.get_top_categories(user, days=days),
            'monthly_trend': AnalyticsService.get_monthly_trend(user),
        }
    
    @staticmethod
    def get_weekly_comparison(user):
        """Compare this week vs last week spending"""
        today = datetime.now().date()
        this_week_start = today - timedelta(days=today.weekday())
        last_week_start = this_week_start - timedelta(days=7)
        
        this_week_total = user.expense_set.filter(date__gte=this_week_start).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        last_week_total = user.expense_set.filter(
            date__gte=last_week_start, 
            date__lt=this_week_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        percent_change = 0
        if last_week_total > 0:
            percent_change = ((float(this_week_total) - float(last_week_total)) / float(last_week_total)) * 100
        
        return {
            'this_week': float(this_week_total),
            'last_week': float(last_week_total),
            'percent_change': percent_change
        }
