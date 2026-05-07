# Create your views here.
from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from .forms import (
    ExpenseEditForm,
    ExpenseFilterForm,
    FeedbackForm,
    GoalDepositForm,
    SavingGoalForm,
    StyledSignUpForm,
    BudgetCycleForm,
)
from .models import BudgetCycle, Expense, Feedback, SavingGoal, Category
from .services.alert_service import check_threshold, trigger_alert
from .services.analytics_service import (
    AnalyticsService,
    BarChartStrategy,
    LineChartStrategy,
    PieChartStrategy,
)
from .services.budget_service import (
    BudgetCalculator,
    calculate_daily_average,
    create_budget_cycle,
    recalculate_daily_limit,
    reset_budget_cycle,
)
from .services.expense_service import ExpenseService

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
    if request.method == 'POST':
        amount = request.POST.get('amount')
        category_choice = request.POST.get('category')
        new_category_name = request.POST.get('new_category_name')
        description = request.POST.get('description')
        date_val = request.POST.get('date') or timezone.now().date()

        # Logic for new category
        if category_choice == "__new__" and new_category_name:
            category_obj, created = Category.objects.get_or_create(name=new_category_name)
        else:
            category_obj, created = Category.objects.get_or_create(name=category_choice)

        Expense.objects.create(
            user=request.user,
            category=category_obj,
            amount=amount,
            description=description,
            date=date_val
        )
        return redirect('dashboard')
    
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

    goals = SavingGoal.objects.filter(user=request.user)
    
    # Budget Cycle data (US5, US6)
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    daily_limit = None
    daily_average_budget = None
    alert = None
    budget_exceeded = False
    over_budget_amount = None
    if cycle:
        cycle = BudgetCalculator.apply_daily_rollover(cycle)
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
        'active_goals': goals.filter(is_completed=False)[:3],
    }
    return render(request, 'dashboard.html', context)

@login_required
def expense_list(request):
    expenses = ExpenseService.get_user_expenses(request.user)
    form = ExpenseFilterForm(request.GET or None)

    if form.is_valid():
        category = form.cleaned_data.get("category")
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")

        if category:
            expenses = expenses.filter(category=category)
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

    return render(request, 'history.html', {
        'expenses': expenses,
        'filter_form': form,
    })

@login_required
def delete_expense(request, expense_id):
    """Delete an expense"""
    if ExpenseService.delete_expense(expense_id, request.user):
        messages.success(request, 'Expense deleted successfully!')
    else:
        messages.error(request, ' Expense not found or access denied')
    return redirect('history')

@login_required
def edit_expense(request, expense_id):
    expense = ExpenseService.get_expense_by_id(expense_id, request.user)
    if not expense:
        messages.error(request, "Expense not found or access denied.")
        return redirect("history")

    if request.method == "POST":
        form = ExpenseEditForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            cycle = BudgetCycle.objects.filter(user=request.user).last()
            if cycle:
                BudgetCalculator.apply_daily_rollover(cycle)
            messages.success(request, "Expense updated successfully!")
            return redirect("history")
    else:
        form = ExpenseEditForm(instance=expense)

    return render(request, "edit_expense.html", {"form": form, "expense": expense})
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


@login_required
def goals_list(request):
    goals = SavingGoal.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "Goals.html", {"goals": goals})


@login_required
def add_goal(request):
    if request.method == "POST":
        form = SavingGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, "Goal created successfully!")
            return redirect("goals")
    else:
        form = SavingGoalForm()
    return render(request, "add_goal.html", {"form": form})


@login_required
def deposit_goal(request, goal_id):
    goal = SavingGoal.objects.filter(id=goal_id, user=request.user).first()
    if not goal:
        messages.error(request, "Goal not found.")
        return redirect("goals")

    if request.method == "POST":
        form = GoalDepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            goal.current_amount += amount
            if goal.current_amount >= goal.target_amount:
                goal.current_amount = goal.target_amount
                goal.is_completed = True
            goal.save()

            category, _ = Category.objects.get_or_create(name="Savings/Goals")
            Expense.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                description=f"Deposit to goal: {goal.title}",
                date=timezone.now()
            )
            messages.success(request, "Deposit added to goal and recorded as expense.")
            return redirect("goals")
    else:
        form = GoalDepositForm()

    return render(request, "goal_deposit.html", {"goal": goal, "form": form})

    if form.is_valid():
        amount = form.cleaned_data["amount"]
        goal.current_amount += amount
        goal.save()

        # Automatically create an expense linked to this deposit
        category, _ = Category.objects.get_or_create(name="Savings/Goals")
        Expense.objects.create(
            user=request.user,
            category=category,
            amount=amount,
            description=f"Deposit to goal: {goal.title}",
            date=timezone.now()
        )
        messages.success(request, "Deposit recorded and budget updated.")

@login_required
def edit_budget(request):
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    if not cycle:
        messages.error(request, "No budget cycle found. Please set one up first.")
        return redirect('setup')
    if request.method == 'POST':
        form = BudgetCycleForm(request.POST)
        if form.is_valid():
            cycle.total_budget = form.cleaned_data['total_budget']
            cycle.save()
            messages.success(request, 'Budget updated!')
            return redirect('dashboard')
    else:
        form = BudgetCycleForm(initial={'total_budget': cycle.total_budget})
    return render(request, 'edit_budget.html', {'form': form})

@login_required
def delete_goal(request, goal_id):
    goal = SavingGoal.objects.filter(id=goal_id, user=request.user).first()
    if goal:
        goal.delete()
        messages.success(request, "Goal deleted successfully.")
    return redirect("goals")
