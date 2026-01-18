from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic import FormView
from django import forms
from .Login_Authentications import User_Session_Manager
from django.contrib.auth import authenticate
from .User_Lockdown_Mangement import LockdownManagement
from .Security_Config import SIGN_IN_CONFIG
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
import re
from .models import PasswordResetCode
from django.utils import timezone
import hashlib, os
from datetime import timedelta
from email.message import EmailMessage
import smtplib
from django.conf import settings
from django.contrib.auth.hashers import check_password

from Cyber_Course_Project.password_policy import load_password_policy
from Cyber_Course_Project.password_history import is_recent_password, record_password_hash

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

        sql_user = User_Session_Manager.Vulnerable_query_user(username)

        if sql_user and sql_user.check_password(password):
            LockdownManagement.reset_attempts(sql_user)
            return User_Session_Manager.redirect_login(self.request, sql_user, self.success_url)
        
        # Vulnerable raw SQL sign-in - made only to illustrate vulnerability by
        # passive example. The idea is to use "' OR 1=1 -- " or "' OR '1'='1" as password to bypass
        # password check by making the rest of the query a comment.
        # This will log in to the first user in the database.


        sql_user = User_Session_Manager.Vulnerable_Sign_In_query(username, password)
        
        if sql_user:
            return User_Session_Manager.redirect_login(self.request, sql_user, self.success_url)
        
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


def _validate_against_policy(pw: str) -> list[str]:
    """
    Shared validator for reset-password + change-password.
    Returns a list of human-readable errors (for messages.error()).
    """
    p = load_password_policy()
    errs: list[str] = []

    # Length
    if len(pw) < p.min_length:
        errs.append(f"Password must be at least {p.min_length} characters long.")
    if len(pw) > p.max_length:
        errs.append(f"Password must be no more than {p.max_length} characters long.")

    # Counts
    upper = len(re.findall(r"[A-Z]", pw))
    lower = len(re.findall(r"[a-z]", pw))
    digits = len(re.findall(r"\d", pw))
    special = len(re.findall(r"[" + re.escape(p.special_chars) + r"]", pw))

    if p.require_uppercase and upper < p.min_uppercase:
        errs.append(f"Password must contain at least {p.min_uppercase} uppercase letter(s).")
    if p.require_lowercase and lower < p.min_lowercase:
        errs.append(f"Password must contain at least {p.min_lowercase} lowercase letter(s).")
    if p.require_digits and digits < p.min_digits:
        errs.append(f"Password must contain at least {p.min_digits} digit(s).")
    if p.require_special_chars and special < p.min_special_chars:
        errs.append(
            f"Password must contain at least {p.min_special_chars} special character(s) from: {p.special_chars}"
        )

    # Forbidden patterns (include which one matched)
    for pat in p.forbidden_patterns:
        if isinstance(pat, str) and pat and pat.lower() in pw.lower():
            errs.append(f"Password cannot contain the forbidden pattern: '{pat}'.")

    # Repeated characters in a row (if max=2 => forbid 3+ in a row)
    if re.search(r"(.)\1{" + str(p.max_repeated_chars) + r",}", pw):
        errs.append(f"Password cannot contain more than {p.max_repeated_chars} repeated characters in a row.")

    return errs


def reset_password(request):
    """
    GET: render form to submit email, code, and new password.
    POST: validate code not used and not expired (15 minutes); set new password.
    Uses JSON-driven policy + password history.
    """
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

        # Policy validation (JSON-driven)
        policy_errors = _validate_against_policy(new_password)
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

        if timezone.now() - token.created_at > timedelta(minutes=15):
            messages.error(request, "This reset code has expired.")
            return render(request, 'reset_password.html')

        # Password history enforcement (N from JSON)
        if is_recent_password(user, new_password):
            messages.error(request, "You cannot reuse one of your most recent passwords.")
            return render(request, 'reset_password.html')

        old_hash = user.password
        user.set_password(new_password)
        user.save()

        if old_hash:
            record_password_hash(user, old_hash)

        token.used = True
        token.save(update_fields=["used"])

        messages.success(request, "Password has been reset. Please sign in.")
        return redirect('/Sign_In/')

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
    Change Password using the same JSON policy + password history rules.
    """
    if request.method == "POST":
        current_password = request.POST.get("current_password") or ""
        new_password = request.POST.get("new_password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if not current_password or not new_password or not confirm_password:
            messages.error(request, "All fields are required.")
            return render(request, "change_password.html")

        user = request.user
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, "change_password.html")

        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return render(request, "change_password.html")

        # Policy validation (JSON-driven)
        policy_errors = _validate_against_policy(new_password)
        if policy_errors:
            for err in policy_errors:
                messages.error(request, err)
            return render(request, "change_password.html")

        # Password history validation (JSON-driven)
        if is_recent_password(user, new_password):
            messages.error(request, "You cannot reuse one of your most recent passwords.")
            return render(request, "change_password.html")

        old_hash = user.password
        user.set_password(new_password)
        user.save()

        if old_hash:
            record_password_hash(user, old_hash)

        update_session_auth_hash(request, user)
        messages.success(request, "Password changed successfully.")
        return render(request, "change_password.html")

    return render(request, "change_password.html")


