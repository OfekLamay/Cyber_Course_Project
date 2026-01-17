from django import forms
from django.core.exceptions import ValidationError
import re

from Cyber_Course_Project.password_policy import load_password_policy

class SendResetCodeForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        # Don’t leak account existence to the UI; but validate format.
        return email

class VerifyCodeForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))
    code = forms.CharField(min_length=40, max_length=40, widget=forms.TextInput(attrs={"placeholder": "40-char code"}))

    def clean(self):
        cleaned = super().clean()
        cleaned["email"] = cleaned.get("email", "").strip()
        cleaned["code"] = cleaned.get("code", "").strip()
        return cleaned

class ResetPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))
    code = forms.CharField(min_length=40, max_length=40, widget=forms.TextInput())
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "New password"}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"}))

    def clean(self):
        cleaned = super().clean()

        # Support common field names without hardcoding your template expectations
        new_pw = cleaned.get("new_password") or cleaned.get("new_password1")
        confirm = cleaned.get("confirm_password") or cleaned.get("new_password2")

        if new_pw is None:
            return cleaned  # field-level required validation will handle missing

        if confirm is not None and new_pw != confirm:
            raise ValidationError("Passwords do not match.")

        policy = load_password_policy()

        # Length checks
        if len(new_pw) < policy.min_length:
            raise ValidationError(f"Password must be at least {policy.min_length} characters.")
        if len(new_pw) > policy.max_length:
            raise ValidationError(f"Password must be at most {policy.max_length} characters.")

        # Character class counts
        upper = len(re.findall(r"[A-Z]", new_pw))
        lower = len(re.findall(r"[a-z]", new_pw))
        digits = len(re.findall(r"\d", new_pw))
        special = len(re.findall(r"[" + re.escape(policy.special_chars) + r"]", new_pw))

        if policy.require_uppercase and upper < policy.min_uppercase:
            raise ValidationError(f"Password must contain at least {policy.min_uppercase} uppercase letter(s).")
        if policy.require_lowercase and lower < policy.min_lowercase:
            raise ValidationError(f"Password must contain at least {policy.min_lowercase} lowercase letter(s).")
        if policy.require_digits and digits < policy.min_digits:
            raise ValidationError(f"Password must contain at least {policy.min_digits} digit(s).")
        if policy.require_special_chars and special < policy.min_special_chars:
            raise ValidationError(
                f"Password must contain at least {policy.min_special_chars} special character(s)."
            )

        # Forbidden patterns
        for pat in policy.forbidden_patterns:
            if isinstance(pat, str) and pat and pat.lower() in new_pw.lower():
                raise ValidationError("Password contains a forbidden pattern.")

        # Max repeated chars in a row (e.g., max_repeated_chars=2 forbids 'aaa')
        # pattern: any char repeated (max+1) times consecutively
        if re.search(r"(.)\1{" + str(policy.max_repeated_chars) + r",}", new_pw):
            raise ValidationError(
                f"Password cannot contain more than {policy.max_repeated_chars} repeated characters in a row."
            )

        return cleaned