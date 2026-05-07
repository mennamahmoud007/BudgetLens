from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.setup_view, name='setup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('add/', views.add_expense, name='add_expense'),
    path('history/', views.expense_list, name='history'),
    path('edit/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('reset/', views.reset_cycle_view, name='reset_cycle'),
    path('signup/', views.signup_view, name='signup'),
    path("login/", auth_views.LoginView.as_view(authentication_form=views.StyledLoginForm, template_name='registration/login.html'), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path('feedback/', views.feedback_view, name='feedback'),
    path('chatbot/', views.chatbot_response, name='chatbot'),
    path("goals/", views.goals_list, name="goals"),
    path("goals/add/", views.add_goal, name="add_goal"),
    path("goals/<int:goal_id>/deposit/", views.deposit_goal, name="deposit_goal"),
    path('budget/edit/', views.edit_budget, name='edit_budget'),
    path("goals/<int:goal_id>/delete/", views.delete_goal, name="delete_goal"),
]