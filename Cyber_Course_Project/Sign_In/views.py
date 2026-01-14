from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import FormView
from django import forms
from .Login_Authentications import User_Session_Manager
from django.contrib.auth import authenticate
from .User_Lockdown_Mangement import LockdownManagement
from .Security_Config import SIGN_IN_CONFIG

#ADI#
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
import json
import re
from django.conf import settings as dj_settings
from .models import PasswordResetCode
from django.utils import timezone
import hashlib, os
from datetime import timedelta
from email.message import EmailMessage
import smtplib
from django.conf import settings

class SignInForm(forms.Form):
   
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class SignInView(FormView):

    template_name = 'Sign_In.html'
    form_class = SignInForm
    success_url = '/home/'

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            user_obj = None

        if user_obj and LockdownManagement.is_user_locked(user_obj):
            messages.error(
                self.request,
                f"Account temporarily locked due to {SIGN_IN_CONFIG['max_attempts']} failed attempts."
            )
            return self.form_invalid(form)

        user = authenticate(self.request, username=username, password=password)

        if user:
            LockdownManagement.reset_attempts(user)
            return User_Session_Manager.redirect_login(
                self.request, user, self.success_url
            )
        else:

            if user_obj:
                LockdownManagement.register_failed_attempt(user_obj)


            messages.error(self.request, "Invalid username or password")
            return self.form_invalid(form)
        
        
def forgot_password(request):
    """
    GET: render forgot password form.
    POST: generate SHA-1 code, save token, send email; code valid for 15 minutes.
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Please enter your account email.")
            return render(request, 'forgot_password.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Do not reveal existence; still show success message
            messages.success(request, "If an account exists, a reset code was sent.")
            return render(request, 'forgot_password.html')

        # Generate SHA-1 code using username + timestamp + random salt
        salt = os.urandom(16)
        payload = f"{user.username}:{timezone.now().timestamp()}".encode() + salt
        code = hashlib.sha1(payload).hexdigest()

        PasswordResetCode.objects.create(user=user, code=code)

        # Send email using SMTP settings from environment (compatible with Send-Mail/.env)
        _SMTP_HOST = settings.SMTP_HOST
        _SMTP_PORT = settings.SMTP_PORT
        _SMTP_USERNAME = settings.SMTP_USERNAME
        _SMTP_PASSWORD = settings.SMTP_PASSWORD
        _SMTP_USE_TLS = settings.SMTP_USE_TLS
        _FROM_EMAIL = settings.FROM_EMAIL

        subject = "Your password reset code"
        plain = (
            "Hi,\n\n"
            "We received a request to reset the password for your account.\n\n"
            f"Your code: {code}\n"
            "This code expires in 15 minutes.\n\n"
            "If you didn’t request this, you can ignore this email.\n\n"
        )

        if _SMTP_HOST:
            try:
                msg = EmailMessage()
                msg["Subject"] = subject
                msg["From"] = _FROM_EMAIL
                msg["To"] = email
                msg.set_content(plain)

                with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
                    if _SMTP_USE_TLS:
                        server.starttls()
                    if _SMTP_USERNAME and _SMTP_PASSWORD:
                        server.login(_SMTP_USERNAME, _SMTP_PASSWORD)
                    server.send_message(msg)
            except Exception as e:
                messages.error(request, f"Failed to send email: {e}")
                return render(request, 'forgot_password.html')

        messages.success(request, "If an account exists, a reset code was sent.")
        return render(request, 'forgot_password.html')

    return render(request, 'forgot_password.html')


def reset_password(request):
    """
    GET: render form to submit email, code, and new password.
    POST: validate code not used and not expired (15 minutes); set new password.
    """
    def _load_password_config():
        try:
            config_path = os.path.join(dj_settings.BASE_DIR, 'config', 'password_config.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {
                "password_policy": {
                    "min_length": 8,
                    "max_length": 128,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_digits": True,
                    "require_special_chars": True,
                    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                    "forbidden_patterns": [],
                    "max_repeated_chars": 2,
                }
            }

    def _validate_password_policy(password: str):
        cfg = _load_password_config()
        policy = cfg.get('password_policy', {})
        errors = []

        min_length = policy.get('min_length', 8)
        max_length = policy.get('max_length', 128)
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long.")
        if len(password) > max_length:
            errors.append(f"Password must be no more than {max_length} characters long.")

        if policy.get('require_uppercase') and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter.")
        if policy.get('require_lowercase') and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter.")
        if policy.get('require_digits') and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one digit.")

        if policy.get('require_special_chars'):
            special_chars = policy.get('special_chars', '!@#$%^&*()_+-=[]{}|;:,.<>?')
            if not re.search(f'[{re.escape(special_chars)}]', password):
                errors.append(f"Password must contain at least one special character: {special_chars}")

        for pattern in policy.get('forbidden_patterns', []):
            if pattern.lower() in password.lower():
                errors.append(f"Password cannot contain common pattern: {pattern}")

        max_repeated = policy.get('max_repeated_chars', 2)
        for i in range(len(password) - max_repeated):
            if len(set(password[i:i+max_repeated+1])) == 1:
                errors.append(f"Password cannot have more than {max_repeated} repeated characters in a row.")

        return errors

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        code = request.POST.get("code", "").strip()
        new_password = request.POST.get("new_password", "")
        confirm = request.POST.get("confirm_password", "")

        if not (email and code and new_password and confirm):
            messages.error(request, "All fields are required.")
            return render(request, 'reset_password.html')

        if new_password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'reset_password.html')

        # Validate password against config policy
        policy_errors = _validate_password_policy(new_password)
        if policy_errors:
            for err in policy_errors:
                messages.error(request, err)
            return render(request, 'reset_password.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or code.")
            return render(request, 'reset_password.html')

        try:
            token = PasswordResetCode.objects.filter(user=user, code=code, used=False).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            messages.error(request, "Invalid email or code.")
            return render(request, 'reset_password.html')

        # Check expiry: 15 minutes
        if timezone.now() - token.created_at > timedelta(minutes=15):
            messages.error(request, "This reset code has expired.")
            return render(request, 'reset_password.html')

        # Set new password securely
        user.set_password(new_password)
        user.save()
        token.used = True
        token.save(update_fields=["used"])

        messages.success(request, "Password has been reset. Please sign in.")
        return redirect('/Sign_In/')
    # GET: optionally prefill email/code from query string
    prefill_email = request.GET.get("email", "")
    prefill_code = request.GET.get("code", "")
    return render(request, 'reset_password.html', {"prefill_email": prefill_email, "prefill_code": prefill_code})


def verify_code(request):
    """
    POST: Validate the provided email + code. If valid (not used and <15 min), redirect to reset-password
    with email and code in the query string. Otherwise, render forgot page with an error.
    """
    if request.method != "POST":
        return redirect('/Sign_In/forgot-password/')

    email = request.POST.get("email", "").strip()
    code = request.POST.get("code", "").strip()

    if not (email and code):
        messages.error(request, "Email and code are required.")
        return render(request, 'forgot_password.html')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "Invalid email or code.")
        return render(request, 'forgot_password.html')

    try:
        token = PasswordResetCode.objects.filter(user=user, code=code, used=False).latest('created_at')
    except PasswordResetCode.DoesNotExist:
        messages.error(request, "Invalid email or code.")
        return render(request, 'forgot_password.html')

    if timezone.now() - token.created_at > timedelta(minutes=15):
        messages.error(request, "This reset code has expired. Please request a new code.")
        return render(request, 'forgot_password.html')

    # Valid code: redirect to reset page with email+code in query string
    return redirect(f"/Sign_In/reset-password/?email={email}&code={code}")

#ADI#
@login_required
def change_password(request):
    """
    Handles the Change Password screen.

    GET  -> render the change_password.html form
    POST -> validate current password and update to a new one
    """

    # If the user submitted the form (POST request)
    if request.method == "POST":
        # Read form fields from the POST data
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        #  Basic validation: all fields must be filled
        if not current_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request, "change_password.html")

        #  New password and confirmation must match
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return render(request, "change_password.html")

        #  Check that the current password is correct for the logged-in user
        user = request.user
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, "change_password.html")


        # Update the password securely using Django's built-in method
        user.set_password(new_password)
        user.save()

        #  Keep the user logged in after the password change
        update_session_auth_hash(request, user)

        #  Show success message to the user
        messages.success(request, "Password changed successfully.")
        return render(request, "change_password.html")

    # If this is a GET request, simply render the form
    return render(request, "change_password.html")
