from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings as dj_settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from email.message import EmailMessage
from django.urls import reverse

import os
import smtplib
import hashlib
from datetime import timedelta

from Sign_In.models import PasswordResetCode  # uses existing model

def forgot_password(request):
    """
    GET: render forgot form
    POST: generate code (SHA-1), store, send email (15 min validity)
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        if not email:
            messages.error(request, "Please enter your account email.")
            return render(request, 'forgot_password.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # do not reveal existence
            messages.success(request, "If an account exists, a reset code was sent.")
            return render(request, 'forgot_password.html')

        # generate SHA-1 code
        salt = os.urandom(16)
        payload = f"{user.username}:{timezone.now().timestamp()}".encode() + salt
        code = hashlib.sha1(payload).hexdigest()

        PasswordResetCode.objects.create(user=user, code=code)

        # SMTP settings (compatible with existing settings)
        _SMTP_HOST = getattr(dj_settings, 'SMTP_HOST', None)
        _SMTP_PORT = getattr(dj_settings, 'SMTP_PORT', 587)
        _SMTP_USERNAME = getattr(dj_settings, 'SMTP_USERNAME', None)
        _SMTP_PASSWORD = getattr(dj_settings, 'SMTP_PASSWORD', None)
        _SMTP_USE_TLS = getattr(dj_settings, 'SMTP_USE_TLS', True)
        _FROM_EMAIL = getattr(dj_settings, 'FROM_EMAIL', 'no-reply@example.com')
        _FRONTEND_URL = getattr(dj_settings, 'FRONTEND_URL', 'http://127.0.0.1:8000/Forgot_Password')

        subject = "Your password reset code"
        plain = (
            "Hi,\n\n"
            "We received a request to reset the password for your account.\n\n"
            f"Your code: {code}\n"
            "This code expires in 15 minutes.\n\n"
            "If you didn’t request this, you can ignore this email.\n\n"
            "You can also paste the code in the website. Reset link (if supported):\n"
            f"{_FRONTEND_URL}/reset-password?email={email}&code={code}\n\n"
            "Thanks,\nThe Team\n"
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


def verify_code(request):
    """
    POST: validate email+code, ensure not used and <15 min old; redirect to reset-password
    """
    if request.method != "POST":
        return redirect('/Forgot_Password/forgot-password/')

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

    if token.created_at < timezone.now() - timedelta(minutes=15):
        messages.error(request, "This code has expired. Please request a new one.")
        return render(request, 'forgot_password.html')

    # ok, redirect with params
    url = reverse('Forgot_Password:reset_password')
    return redirect(f"{url}?email={email}&code={code}")


def reset_password(request):
    """
    GET: render reset form (prefill from query)
    POST: validate code and set new password
    Note: keep minimal checks to avoid changing other vulnerabilities.
    """
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        code = request.POST.get("code", "").strip()
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not (email and code and new_password and confirm_password):
            messages.error(request, "All fields are required.")
            return render(request, 'reset_password.html')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
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

        if token.created_at < timezone.now() - timedelta(minutes=15):
            messages.error(request, "This code has expired. Please request a new one.")
            return render(request, 'reset_password.html')

        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=['password'])
            token.used = True
            token.save(update_fields=['used'])

        messages.success(request, "Your password has been updated. You may now sign in.")
        return redirect('/Sign_In/')

    # GET
    prefill_email = request.GET.get("email", "")
    prefill_code = request.GET.get("code", "")
    return render(request, 'reset_password.html', {"prefill_email": prefill_email, "prefill_code": prefill_code})