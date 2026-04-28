from django.urls import path
from . import views

urlpatterns = [
    path('', views.setup_view),
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_expense, name='add_expense'),
    path('list/', views.expense_list, name='expense_list'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
]
