# Create your views here.
from django.shortcuts import render

# =============================
# Setup Views (US1)
# =============================

def setup_view(request):
    return render(request, 'setup.html')


# =============================
# Expense Views (US2)
# =============================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.expense_service import ExpenseService
from .services.analytics_service import AnalyticsService
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
    
    return render(request, 'budget_app/add_expense.html')

@login_required
def dashboard(request):
    """Dashboard with insights and charts - uses AnalyticsService"""
    # Get filter from URL (default 30 days)
    days = int(request.GET.get('days', 30))
    
    # Use Analytics Service for all data
    context = AnalyticsService.get_spending_summary(request.user, days=days)
    
    # Add recent expenses
    context['recent_expenses'] = ExpenseService.get_user_expenses(request.user, limit=10)
    context['selected_days'] = days
    
    # Add weekly comparison for extra insight
    context['weekly_comparison'] = AnalyticsService.get_weekly_comparison(request.user)
    
    return render(request, 'budget_app/dashboard.html', context)

@login_required
def expense_list(request):
    """View all expenses"""
    expenses = ExpenseService.get_user_expenses(request.user)
    return render(request, 'budget_app/expense_list.html', {'expenses': expenses})

@login_required
def delete_expense(request, expense_id):
    """Delete an expense"""
    if ExpenseService.delete_expense(expense_id, request.user):
        messages.success(request, 'Expense deleted successfully!')
    else:
        messages.error(request, ' Expense not found or access denied')
    return redirect('expense_list')


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
