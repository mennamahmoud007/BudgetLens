# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse

# =============================
# Setup Views (US1)
# =============================

def setup_view(request):
    return render(request, 'setup.html')


# =============================
# Expense Views (US2)
# =============================

<<<<<<< HEAD
def add_expense_view(request):
    return HttpResponse("Add Expense Page - To be implemented")
=======
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.expense_service import ExpenseService
from .services.analytics_service import AnalyticsService, BarChartStrategy, LineChartStrategy, PieChartStrategy
from django.utils import timezone

@login_required
def add_expense(request):
    """Add a new expense - uses ExpenseService"""
    if request.method == 'POST':
        try:
            # Get data from form
            amount = float(request.POST.get('amount'))
            category_name = request.POST.get('category')
            description = request.POST.get('description')
            date_str = request.POST.get('date')
            
            # Use service to add expense
            expense = ExpenseService.add_expense(
                user=request.user,
                category_name=category_name,
                amount=amount,
                description=description,
                date=date_str if date_str else None
            )
            
            messages.success(request, f'Added: ${expense.amount} for {expense.description}')
            return redirect('dashboard')
            
        except ValueError as e:
            messages.error(request, f'Validation Error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error adding expense: {str(e)}')
    
    return render(request, 'add_expense.html')

@login_required
def dashboard(request):
    """Dashboard with insights and charts - uses AnalyticsService"""
    # Get filter from URL (default 30 days)
    days = int(request.GET.get('days', 30))
    
    analytics = AnalyticsService()
    
    # Get raw data for charts
    spending_by_category = AnalyticsService.get_spending_by_category(request.user, days=days)
    monthly_trend = AnalyticsService.get_monthly_trend(request.user)
    
    # Generate different chart types using Strategy pattern
    analytics.set_strategy(PieChartStrategy())
    pie_chart_data = analytics.get_chart_data(spending_by_category)
    
    analytics.set_strategy(BarChartStrategy())
    bar_chart_data = analytics.get_chart_data(spending_by_category)
    
    analytics.set_strategy(LineChartStrategy())
    line_chart_data = analytics.get_chart_data(monthly_trend)
    context = {
        # Strategy pattern results (charts)
        'pie_chart': pie_chart_data,
        'bar_chart': bar_chart_data,
        'line_chart': line_chart_data,
        
        # Original analytics data
        'by_category': spending_by_category,        
        'monthly_trend': monthly_trend,
        'total_spent': AnalyticsService.get_total_spending(request.user, days),
        'daily_average': AnalyticsService.get_daily_average(request.user, days),
        'top_categories': AnalyticsService.get_top_categories(request.user, days=days),
        
        # Other context
        'recent_expenses': ExpenseService.get_user_expenses(request.user, limit=10),
        'selected_days': days,
        'weekly_comparison': AnalyticsService.get_weekly_comparison(request.user),
    }
    return render(request, 'dashboard.html', context)

@login_required
def expense_list(request):
    """View all expenses"""
    expenses = ExpenseService.get_user_expenses(request.user)
    return render(request, 'expense_list.html', {'expenses': expenses})

@login_required
def delete_expense(request, expense_id):
    """Delete an expense"""
    if ExpenseService.delete_expense(expense_id, request.user):
        messages.success(request, 'Expense deleted successfully!')
    else:
        messages.error(request, ' Expense not found or access denied')
    return redirect('expense_list')
>>>>>>> 449014b8b10bb3389f3212f911c1c72a26a8774f


# =============================
# Dashboard Views (US3,4,5)
# =============================

def dashboard_view(request):
    pass


# =============================
# History Views (US7)
# =============================

def history_view(request):
    pass
