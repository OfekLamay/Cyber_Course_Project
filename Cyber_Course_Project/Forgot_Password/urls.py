from django.urls import path
from . import views

app_name = "Forgot_Password"

urlpatterns = [
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("reset-password/", views.reset_password, name="reset_password"),
]