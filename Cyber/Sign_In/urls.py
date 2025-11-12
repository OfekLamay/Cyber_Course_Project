from django.urls import path
from . import views

urlpatterns = [
    path('', views.Sign_In_view, name='Sign_In'),
    # remove path after making vulnerable version of the project
    path('sql_injection/', views.Sql_Injection_login_view, name='Sql_Injection_Login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
]