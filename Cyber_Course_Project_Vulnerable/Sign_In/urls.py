from django.urls import path
from . import views

urlpatterns = [
    path('', views.SignInView.as_view(), name='Sign_In'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('verify-code/', views.verify_code, name='verify_code'),
]