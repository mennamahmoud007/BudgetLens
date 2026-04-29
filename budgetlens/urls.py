from django.urls import path
#from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from budget_app.views import StyledLoginForm
from budget_app import views
urlpatterns = [ 
    # path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # for login/logout
    path('', include('budget_app.urls')),

    path("login/", auth_views.LoginView.as_view(
        authentication_form=StyledLoginForm
    ), name="login"),
     path('accounts/signup/', views.signup_view, name='signup'),
     path('feedback/', views.feedback_view, name='feedback'),
     path('feedback/', views.feedback_view, name='feedback'),
     path('chatbot/', views.chatbot_response, name='chatbot'),
]
