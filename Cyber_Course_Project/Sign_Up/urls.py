from django.urls import path
from . import views

urlpatterns = [
    path('', views.Sign_Up_view, name='Sign_Up'),
]