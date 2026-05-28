from budget_app.models import Expense, Category
from django.utils import timezone
from decimal import Decimal, InvalidOperation


class ExpenseService:

    @staticmethod
    def add_expense(user, category_name, amount, description, date=None):
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise ValueError("Amount must be a valid number.")
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        if not description or not description.strip():
            raise ValueError("Description cannot be empty.")
        category, _ = Category.objects.get_or_create(name=category_name.strip().capitalize())
        return Expense.objects.create(
            user=user,
            category=category,
            amount=amount,
            description=description.strip(),
            date=date if date else timezone.now().date(),
        )

    @staticmethod
    def get_user_expenses(user, limit=None):
        expenses = Expense.objects.filter(user=user).select_related('category').order_by('-date')
        if limit:
            expenses = expenses[:limit]
        return expenses

    @staticmethod
    def get_expense_by_id(expense_id, user):
        try:
            return Expense.objects.get(id=expense_id, user=user)
        except Expense.DoesNotExist:
            return None

    @staticmethod
    def delete_expense(expense_id, user):
        expense = ExpenseService.get_expense_by_id(expense_id, user)
        if expense:
            expense.delete()
            return True
        return False