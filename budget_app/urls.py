from django.urls import path
from . import views

urlpatterns = [
    path('', views.setup_view, name='setup'),
    path('accounts/signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('add/', views.add_expense, name='add_expense'),
    path('history/', views.expense_list, name='history'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
]
