from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum
from collections import defaultdict

from reportlab.pdfgen import canvas

from .models import BudgetCycle, Expense, Feedback, SavingGoal, Category
from .forms import (
    ExpenseEditForm,
    ExpenseFilterForm,
    FeedbackForm,
    GoalDepositForm,
    SavingGoalForm,
    StyledSignUpForm,
    BudgetCycleForm,
)
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


def signup_view(request):
    if request.method == "POST":
        form = StyledSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to BudgetLens! Set up your first budget cycle below.")
            return redirect('setup')
    else:
        form = StyledSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

signup = signup_view


@login_required
def setup_view(request):
    if request.method == 'POST':
        form = BudgetCycleForm(request.POST)
        if form.is_valid():
            create_budget_cycle(
                request.user,
                form.cleaned_data['total_budget'],
                form.cleaned_data.get('start_date'),
                form.cleaned_data.get('end_date'),
            )
            messages.success(request, 'Budget cycle created successfully!')
            return redirect('dashboard')
    else:
        form = BudgetCycleForm()
    return render(request, 'setup.html', {'form': form})


@login_required
def dashboard(request):
    days = int(request.GET.get('days', 30))

    spending_by_category = AnalyticsService.get_spending_by_category(request.user, days=days)
    monthly_trend = AnalyticsService.get_monthly_trend(request.user)

    analytics = AnalyticsService()
    analytics.set_strategy(PieChartStrategy())
    pie_chart_data = analytics.get_chart_data(spending_by_category)
    analytics.set_strategy(BarChartStrategy())
    bar_chart_data = analytics.get_chart_data(spending_by_category)
    analytics.set_strategy(LineChartStrategy())
    line_chart_data = analytics.get_chart_data(monthly_trend)

    cycle = BudgetCycle.objects.filter(user=request.user).last()

    daily_limit = None
    daily_average_budget = None
    alert = None
    budget_exceeded = False
    over_budget_amount = Decimal("0.00")
    total_budget = Decimal("0.00")
    spent = Decimal("0.00")
    remaining_budget = Decimal("0.00")

    if cycle:
        cycle = BudgetCalculator.apply_daily_rollover(cycle)
        daily_limit = cycle.daily_limit
        daily_average_budget = calculate_daily_average(cycle)
        total_budget = cycle.total_budget
        spent = cycle.spent
        remaining_budget = cycle.remaining_budget

        if spent > total_budget:
            budget_exceeded = True
            over_budget_amount = spent - total_budget

        if check_threshold(spent, total_budget):
            alert = trigger_alert()

    context = {
        'pie_chart': pie_chart_data,
        'bar_chart': bar_chart_data,
        'line_chart': line_chart_data,
        'by_category': spending_by_category,
        'monthly_trend': monthly_trend,
        'total_spent': AnalyticsService.get_total_spending(request.user, days),
        'daily_average': AnalyticsService.get_daily_average(request.user, days),
        'top_categories': AnalyticsService.get_top_categories(request.user, days=days),
        'weekly_comparison': AnalyticsService.get_weekly_comparison(request.user),
        'cycle': cycle,
        'total_budget': total_budget,
        'spent': spent,
        'remaining_budget': remaining_budget,
        'daily_limit': daily_limit,
        'daily_average_budget': daily_average_budget,
        'budget_exceeded': budget_exceeded,
        'over_budget_amount': over_budget_amount,
        'alert': alert,
        'recent_expenses': ExpenseService.get_user_expenses(request.user, limit=10),
        'selected_days': days,
        'active_goals': SavingGoal.objects.filter(user=request.user, is_completed=False)[:3],
    }
    return render(request, 'dashboard.html', context)


@login_required
def add_expense(request):
    if request.method == 'POST':
        amount_raw = request.POST.get('amount', '').strip()
        category_choice = request.POST.get('category', '').strip()
        new_category_name = request.POST.get('new_category_name', '').strip()
        description = request.POST.get('description', '').strip()
        date_val = request.POST.get('date') or timezone.now().date()

        try:
            amount = Decimal(amount_raw)
            if amount <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            messages.error(request, "Please enter a valid positive amount.")
            return render(request, 'add_expense.html')

        if category_choice == "__new__" and new_category_name:
            category_obj, _ = Category.objects.get_or_create(name=new_category_name.capitalize())
        elif category_choice:
            category_obj, _ = Category.objects.get_or_create(name=category_choice)
        else:
            category_obj, _ = Category.objects.get_or_create(name="Uncategorized")

        Expense.objects.create(
            user=request.user,
            category=category_obj,
            amount=amount,
            description=description or "No description",
            date=date_val,
        )

        cycle = BudgetCycle.objects.filter(user=request.user).last()
        if cycle:
            BudgetCalculator.apply_daily_rollover(cycle)

        messages.success(request, "Expense added successfully!")
        return redirect('dashboard')

    return render(request, 'add_expense.html')


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
    return render(request, 'history.html', {'expenses': expenses, 'filter_form': form})


@login_required
def delete_expense(request, expense_id):
    if ExpenseService.delete_expense(expense_id, request.user):
        cycle = BudgetCycle.objects.filter(user=request.user).last()
        if cycle:
            BudgetCalculator.apply_daily_rollover(cycle)
        messages.success(request, 'Expense deleted successfully!')
    else:
        messages.error(request, 'Expense not found or access denied.')
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
def edit_budget(request):
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    if not cycle:
        messages.error(request, "No budget cycle found. Please set one up first.")
        return redirect('setup')
    if request.method == 'POST':
        form = BudgetCycleForm(request.POST)
        if form.is_valid():
            cycle.total_budget = form.cleaned_data['total_budget']
            cycle.save(update_fields=['total_budget'])
            BudgetCalculator.apply_daily_rollover(cycle)
            messages.success(request, 'Budget updated successfully!')
            return redirect('dashboard')
    else:
        form = BudgetCycleForm(initial={'total_budget': cycle.total_budget})
    return render(request, 'edit_budget.html', {'form': form})


@login_required
def reset_cycle_view(request):
    if request.method == "POST":
        reset_budget_cycle(request.user)
        messages.success(request, "Budget cycle reset successfully!")
        return redirect('setup')
    return redirect('dashboard')


@login_required
def alerts_view(request):
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    alert = None
    budget_exceeded = False
    over_budget_amount = Decimal("0.00")
    if cycle:
        spent = cycle.spent
        if spent > cycle.total_budget:
            budget_exceeded = True
            over_budget_amount = spent - cycle.total_budget
        elif check_threshold(spent, cycle.total_budget):
            alert = trigger_alert()
    return render(request, 'alerts.html', {
        'alert': alert,
        'cycle': cycle,
        'budget_exceeded': budget_exceeded,
        'over_budget_amount': over_budget_amount,
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
                date=timezone.now().date(),
            )
            cycle = BudgetCycle.objects.filter(user=request.user).last()
            if cycle:
                BudgetCalculator.apply_daily_rollover(cycle)
            messages.success(request, "Deposit added successfully.")
            return redirect("goals")
    else:
        form = GoalDepositForm()
    return render(request, "goal_deposit.html", {"goal": goal, "form": form})


@login_required
def delete_goal(request, goal_id):
    goal = SavingGoal.objects.filter(id=goal_id, user=request.user).first()
    if goal:
        goal.delete()
        messages.success(request, "Goal deleted successfully.")
    return redirect("goals")


def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('feedback')
    else:
        form = FeedbackForm()
    feedbacks = Feedback.objects.all().order_by('-created_at')
    return render(request, 'feedback.html', {'form': form, 'feedbacks': feedbacks})

@login_required
def add_expense(request):
    if request.method == 'POST':
        # ... existing POST logic unchanged ...
        pass

    # ADD THIS to the GET render:
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    return render(request, 'add_expense.html', {'cycle': cycle})

@login_required
def chatbot_response(request):
    message = request.GET.get("message", "").lower()
    cycle = BudgetCycle.objects.filter(user=request.user).last()
    expense_count = Expense.objects.filter(user=request.user).count()

    if "budget" in message:
        if cycle:
            spent = cycle.spent
            if spent > cycle.total_budget:
                reply = f"⚠️ Budget exceeded! Spent ${spent:.2f} of ${cycle.total_budget:.2f}. Over by ${spent - cycle.total_budget:.2f}."
            else:
                reply = f"Budget: ${cycle.total_budget:.2f} | Spent: ${spent:.2f} | Remaining: ${cycle.remaining_budget:.2f}"
            return JsonResponse({"reply": reply})
        return JsonResponse({"reply": "No budget cycle found. Set one up first!"})

    if "expense" in message or "spent" in message:
        return JsonResponse({"reply": f"You have {expense_count} recorded expenses."})

    if "tip" in message:
        return JsonResponse({"reply": "Try to reduce food expenses by 10% this month 💡"})

    if "remaining" in message or "left" in message:
        if cycle:
            return JsonResponse({"reply": f"You have ${cycle.remaining_budget:.2f} remaining."})
        return JsonResponse({"reply": "No active budget cycle."})

    return JsonResponse({"reply": "I can help with budget, expenses, and tips 👍"})


@login_required
def export_weekly_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="BudgetLens_Statement.pdf"'
    p = canvas.Canvas(response)

    end_date = now().date()
    start_date = end_date - timedelta(days=7)
    expenses = Expense.objects.filter(user=request.user, date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

    by_category = defaultdict(float)
    for e in expenses:
        try:
            cat = e.category.name if e.category else "Uncategorized"
            by_category[cat] += float(Decimal(str(e.amount)))
        except (InvalidOperation, ValueError):
            continue

    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(300, 800, "BudgetLens Bank Statement")
    p.setFont("Helvetica", 10)
    p.drawCentredString(300, 785, f"Period: {start_date} to {end_date}")
    p.line(50, 770, 550, 770)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, 740, "Account Summary")
    p.setFont("Helvetica", 12)
    p.drawString(60, 720, f"Total Spending: {total_expenses:.2f} EGP")
    p.drawString(60, 700, f"Transactions: {expenses.count()}")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, 660, "Where Your Money Went")
    y = 630
    p.setFont("Helvetica", 12)
    if not by_category:
        p.drawString(60, y, "No transactions in this period.")
    else:
        for cat, amount in by_category.items():
            p.drawString(60, y, cat)
            p.drawRightString(500, y, f"{amount:.2f} EGP")
            y -= 22
    p.line(50, 80, 550, 80)
    p.setFont("Helvetica-Oblique", 9)
    p.drawCentredString(300, 60, "Auto-generated by BudgetLens")
    p.setFont("Helvetica", 8)
    p.drawCentredString(300, 45, f"Generated on {now().strftime('%Y-%m-%d %H:%M')}")
    p.showPage()
    p.save()
    return response


class StyledLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password'
    }))