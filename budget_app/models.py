# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"{self.description} - ${self.amount}"

 
class BudgetCycle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_budget = models.DecimalField(max_digits=10, decimal_places=2)
    
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
    name = models.CharField(max_length=100, blank=True, null=True)
    message = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:30]


