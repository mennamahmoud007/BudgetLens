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

def add_expense_view(request):
    pass


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