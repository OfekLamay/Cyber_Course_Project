from django.urls import path
from . import views

urlpatterns = [
    path('', views.SignInView.as_view(), name='Sign_In'),
]