# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    """
    Represents a classification for financial transactions (e.g., Food, Rent).
    Used to group expenses for analytical reporting.
    """
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Expense(models.Model):
    """
    Represents an individual financial outflow recorded by a user.
    
    Attributes:
        user: Reference to the User who owns this expense.
        category: The Category assigned to this expense.
        amount: The monetary value of the transaction.
        description: A short text summary of the purchase.
        date: The calendar date the expense occurred.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"

 
class BudgetCycle(models.Model):
    """
    Defines a specific time period (e.g., monthly) with a set spending limit.
    
    Properties:
        spent: Calculates total expenses within this cycle's date range.
        remaining_budget: Calculates the difference between the total budget and spending.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_budget = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_recalculated_date = models.DateField(null=True, blank=True)
    
    @property
    def spent(self):
        return sum(expense.amount for expense in Expense.objects.filter(
            user=self.user,
            date__range=(self.start_date, self.end_date)
        ))
    
    @property
    def remaining_budget(self):
        return self.total_budget - self.spent
    
    def __str__(self):
        return f"Budget Cycle: {self.start_date} to {self.end_date} - ${self.total_budget}"
    
   
class Feedback(models.Model):
    """
    Stores user suggestions and ratings for the application.
    Used for gathering qualitative data on user satisfaction.
    """
    name = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:30]

class SavingGoal(models.Model):
    """
    Tracks progress toward a specific financial target.
    Calculates completion status based on current vs. target amounts.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    @property
    def progress_percent(self):
        if self.target_amount <= 0:
            return 0
        return min(100, int((self.current_amount / self.target_amount) * 100))

    def __str__(self):
        return f"{self.title} ({self.current_amount}/{self.target_amount})"
    
class Transaction(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        type = models.CharField(max_length=10, choices=[
            ('income', 'Income'),
            ('expense', 'Expense'),
        ])
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        date = models.DateField()