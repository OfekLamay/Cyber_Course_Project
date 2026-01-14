from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from email.message import EmailMessage
import smtplib, os, hashlib

from .forms import SendResetCodeForm, VerifyCodeForm, ResetPasswordForm
from django.contrib.auth.models import User
from Sign_In.models import PasswordResetCode  # reuse existing model

RESET_TTL_MINUTES = 15

def _send_email(to_email: str, subject: str, body: str) -> None:
    host = settings.SMTP_HOST
    port = int(getattr(settings, "SMTP_PORT", 587))
    user = getattr(settings, "SMTP_USERNAME", None)
    pwd = getattr(settings, "SMTP_PASSWORD", None)
    use_tls = str(getattr(settings, "SMTP_USE_TLS", "true")).lower() == "true"
    sender = getattr(settings, "FROM_EMAIL", user or "no-reply@example.com")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=10) as s:
        if use_tls:
            s.starttls()
        if user and pwd:
            s.login(user, pwd)
        s.send_message(msg)

def forgot_password(request):
    if request.method == "POST":
        form = SendResetCodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            # Always respond success (don’t leak account existence)
            try:
                user = User.objects.filter(email=email).first()
                if user:
                    rand = os.urandom(16)
                    seed = f"{email}|{timezone.now().timestamp()}".encode("utf-8") + rand
                    code = hashlib.sha1(seed).hexdigest()

                    token = PasswordResetCode.objects.create(
                        user=user, code=code, created_at=timezone.now(), used=False
                    )

                    base = getattr(settings, "FRONTEND_URL", "")
                    reset_link = f"{base}/Sign_In/reset-password/?email={email}&code={code}" if base else \
                                  f"/Forgot_Password/reset-password/?email={email}&code={code}"

                    body = (
                        "You requested a password reset.\n\n"
                        f"Code: {code}\n"
                        f"This code expires in {RESET_TTL_MINUTES} minutes.\n\n"
                    )
                    _send_email(email, "Your password reset code", body)
                messages.success(request, "If an account exists, a reset code was sent.")
            except Exception as e:
                messages.error(request, f"Failed to send email: {e}")
        else:
            messages.error(request, "Please enter a valid email.")
        return redirect("Forgot_Password:forgot_password")

    # GET
    return render(request, "forgot_password.html", {"send_form": SendResetCodeForm(), "verify_form": VerifyCodeForm()})

def verify_code(request):
    if request.method == "POST":
        form = VerifyCodeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            code = form.cleaned_data["code"]
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "Invalid email or code.")
                return redirect("Forgot_Password:forgot_password")

            token = PasswordResetCode.objects.filter(user=user, code=code, used=False).first()
            if not token:
                messages.error(request, "Invalid or already used code.")
                return redirect("Forgot_Password:forgot_password")

            if timezone.now() - token.created_at > timedelta(minutes=RESET_TTL_MINUTES):
                messages.error(request, "This reset code has expired.")
                return redirect("Forgot_Password:forgot_password")

            # Redirect to reset page with prefilled params
            return redirect(f"/Forgot_Password/reset-password/?email={email}&code={code}")
        messages.error(request, "Please enter a valid email and code.")
        return redirect("Forgot_Password:forgot_password")

    # GET just renders the forgot page (no direct GET UI)
    return redirect("Forgot_Password:forgot_password")

def reset_password(request):
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            code = form.cleaned_data["code"]
            new_password = form.cleaned_data["new_password"]

            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, "Invalid email or code.")
                return redirect("Forgot_Password:reset_password")

            token = PasswordResetCode.objects.filter(user=user, code=code, used=False).first()
            if not token:
                messages.error(request, "Invalid or already used code.")
                return redirect("Forgot_Password:reset_password")

            if timezone.now() - token.created_at > timedelta(minutes=RESET_TTL_MINUTES):
                messages.error(request, "This reset code has expired.")
                return redirect("Forgot_Password:reset_password")

            user.set_password(new_password)
            user.save()
            token.used = True
            token.save(update_fields=["used"])
            messages.success(request, "Password has been reset. Please sign in.")
            return redirect("/Sign_In/")
        # invalid form -> show errors
        return render(request, "reset_password.html", {"form": form})

    # GET: prefill email/code from query params
    initial = {
        "email": request.GET.get("email", ""),
        "code": request.GET.get("code", ""),
    }
    return render(request, "reset_password.html", {"form": ResetPasswordForm(initial=initial)})