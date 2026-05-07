from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from budget_app.models import BudgetCycle, Category, Expense
from budget_app.services.alert_service import check_threshold


class BudgetLensTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass12345")
        self.client.login(username="u1", password="pass12345")
        self.category = Category.objects.create(name="Food")
        self.cycle = BudgetCycle.objects.create(
            user=self.user,
            start_date="2026-05-01",
            end_date="2026-05-31",
            total_budget=Decimal("1000.00"),
            remaining_balance=Decimal("1000.00"),
            daily_limit=Decimal("32.25"),
            last_recalculated_date="2026-05-01",
        )

    def test_history_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("history"))
        self.assertNotEqual(response.status_code, 200)

    def test_threshold_check(self):
        self.assertTrue(check_threshold(Decimal("800"), Decimal("1000")))
        self.assertFalse(check_threshold(Decimal("799.99"), Decimal("1000")))

    def test_edit_expense(self):
        exp = Expense.objects.create(
            user=self.user,
            category=self.category,
            amount=Decimal("50.00"),
            description="Lunch",
            date="2026-05-06",
        )
        response = self.client.post(reverse("edit_expense", args=[exp.id]), {
            "amount": "60.00",
            "category": self.category.id,
            "description": "Lunch updated",
            "date": "2026-05-06",
        })
        self.assertEqual(response.status_code, 302)
        exp.refresh_from_db()
        self.assertEqual(exp.amount, Decimal("60.00"))