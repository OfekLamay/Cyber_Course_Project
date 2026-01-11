from django.urls import path
from . import views

urlpatterns = [
    path('', views.SignInView.as_view(), name='Sign_In'),
    # No RedirectView entries here; templates link directly to Forgot_Password app.
]