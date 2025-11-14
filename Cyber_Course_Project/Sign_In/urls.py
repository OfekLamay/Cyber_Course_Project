from django.urls import path
from . import views

urlpatterns = [
    path('', views.Sign_In_view, name='Sign_In'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
]