# Expense service - business logic for expenses
from budget_app.models import Expense, Category
from django.utils import timezone
from decimal import Decimal

class ExpenseService:
    """Business logic for expense operations"""
    
    @staticmethod
    def add_expense(user, category_name, amount, description, date=None):
        """
        Add a new expense with validation
        Returns: Expense object
        Raises: ValueError if validation fails
        """
        # Validation
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        if not description or len(description.strip()) == 0:
            raise ValueError("Description cannot be empty")
        
        # Get or create category
        category, created = Category.objects.get_or_create(
            name=category_name.capitalize()
        )
        
        # Create expense
        expense = Expense.objects.create(
            user=user,
            category=category,
            amount=Decimal(str(amount)),
            description=description.strip(),
            date=date if date else timezone.now().date()
        )
        
        return expense
    
    @staticmethod
    def get_user_expenses(user, limit=None):
        """Get all expenses for a user, ordered by most recent"""
        expenses = Expense.objects.filter(user=user).order_by('-date')        
        if limit:
            expenses = expenses[:limit]
        return expenses
    
    @staticmethod
    def get_expense_by_id(expense_id, user):
        """Get a specific expense if it belongs to the user"""
        try:
            return Expense.objects.get(id=expense_id, user=user)
        except Expense.DoesNotExist:
            return None
    
    @staticmethod
    def delete_expense(expense_id, user):
        """Delete an expense if it belongs to the user"""
        expense = ExpenseService.get_expense_by_id(expense_id, user)
        if expense:
            expense.delete()
            return True
        return False
