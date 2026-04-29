from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from budget_app import views
urlpatterns = [
    path('', views.setup_view, name='setup'),
    path('accounts/signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('add/', views.add_expense, name='add_expense'),
    path('history/', views.expense_list, name='history'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
     path('reset/', views.reset_cycle_view, name='reset_cycle'),
      path('accounts/signup/', views.signup_view, name='signup'),

    path("login/", auth_views.LoginView.as_view(
        authentication_form=views.StyledLoginForm
    ), name="login"),
    path('feedback/', views.feedback_view, name='feedback'),
]

