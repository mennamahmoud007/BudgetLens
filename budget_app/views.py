# Create your views here.
from urllib import request
from .models import Feedback
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import BudgetCycle, Expense
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import BudgetCycle
from .services.expense_service import ExpenseService
from .services.analytics_service import AnalyticsService, BarChartStrategy, LineChartStrategy, PieChartStrategy
from .services.budget_service import recalculate_daily_limit, create_budget_cycle, calculate_daily_average
from .services.alert_service import check_threshold, trigger_alert
from .services.budget_service import reset_budget_cycle

from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import FeedbackForm, StyledSignUpForm
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


from django import forms

class BudgetCycleForm(forms.Form):
    total_budget = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01, label="Monthly Budget Amount")
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="Start Date (optional)")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, label="End Date (optional)")

@login_required
def setup_view(request):
    if request.method == 'POST':
        form = BudgetCycleForm(request.POST)
        if form.is_valid():
            total_budget = form.cleaned_data['total_budget']
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            create_budget_cycle(request.user, total_budget, start_date, end_date)
            messages.success(request, 'Budget cycle created successfully!')
            return redirect('dashboard')
    else:
        form = BudgetCycleForm()
    
    return render(request, 'setup.html', {'form': form})

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
    
    # Budget Cycle data (US5, US6)
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    daily_limit = None
    daily_average_budget = None
    alert = None
    budget_exceeded = False
    over_budget_amount = None
    
    if cycle:
        daily_limit = recalculate_daily_limit(cycle)
        daily_average_budget = calculate_daily_average(cycle)
        
        # Check if budget is exceeded
        if cycle.spent > cycle.total_budget:
            budget_exceeded = True
            over_budget_amount = cycle.spent - cycle.total_budget
        
        # Check if reached 80% threshold
        if check_threshold(cycle.spent, cycle.total_budget):
            alert = trigger_alert()
    
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
        
        # Budget Cycle data
        'daily_limit': daily_limit,
        'daily_average_budget': daily_average_budget,
        'alert': alert,
        'budget_exceeded': budget_exceeded,
        'over_budget_amount': over_budget_amount,
        'cycle': cycle,
        'total_budget': cycle.total_budget if cycle else None,
        'spent': cycle.spent if cycle else None,
        'remaining_budget': cycle.remaining_budget if cycle else None,
        
        # Other context
        'recent_expenses': ExpenseService.get_user_expenses(request.user, limit=10),
        'selected_days': days,
        'weekly_comparison': AnalyticsService.get_weekly_comparison(request.user),
    }
    return render(request, 'dashboard.html', context)

@login_required
def expense_list(request):
    """View all expenses - History"""
    expenses = ExpenseService.get_user_expenses(request.user)
    return render(request, 'history.html', {'expenses': expenses})

@login_required
def delete_expense(request, expense_id):
    """Delete an expense"""
    if ExpenseService.delete_expense(expense_id, request.user):
        messages.success(request, 'Expense deleted successfully!')
    else:
        messages.error(request, ' Expense not found or access denied')
    return redirect('history')

@login_required
def alerts_view(request):
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    alert = None
    if cycle and check_threshold(cycle.spent, cycle.total_budget):
        alert = trigger_alert()
    
    return render(request, 'alerts.html', {'alert': alert, 'cycle': cycle})
@login_required
def reset_cycle_view(request):
    if request.method == "POST":
        reset_budget_cycle(request.user)
        messages.success(request, "Budget cycle reset successfully!")
        return redirect('setup')
    
    return redirect('dashboard')
class StyledLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter username'
    }))

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))
def signup_view(request):
    if request.method == "POST":
        form = StyledSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = StyledSignUpForm()

    return render(request, 'registration/signup.html', {'form': form})

def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('feedback')

    else:
        form = FeedbackForm()

    feedbacks = Feedback.objects.all().order_by('-id')
    feedbacks = Feedback.objects.all().order_by('-created_at')

    return render(request, 'feedback.html', {
        'form': form,
        'feedbacks': feedbacks
    })
@login_required
def chatbot_response(request):
    message = request.GET.get("message", "").lower()

    cycle = BudgetCycle.objects.filter(user=request.user).last()
    total_spent = Expense.objects.filter(user=request.user).count()

    if "budget" in message:
        if cycle:
            return JsonResponse({
                "reply": f"Your total budget is {cycle.total_budget} and you spent {cycle.spent}."
            })
        return JsonResponse({"reply": "No budget found yet."})

    if "expense" in message:
        return JsonResponse({
            "reply": f"You have {total_spent} recorded expenses."
        })

    if "tip" in message:
        return JsonResponse({
            "reply": "Try to reduce food expenses by 10% this month 💡"
        })

    return JsonResponse({
        "reply": "I can help you with budget, expenses, and tips 👍"
    })
