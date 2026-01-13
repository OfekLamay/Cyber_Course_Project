from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from pathlib import Path
import json
import re

class SendResetCodeForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
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
        p1 = cleaned.get("new_password", "") or ""
        p2 = cleaned.get("confirm_password", "") or ""
        if p1 != p2:
            self.add_error("confirm_password", "Passwords do not match.")
        self._validate_password_policy(p1)
        return cleaned

    def _validate_password_policy(self, password: str):
        # Load config: BASE_DIR/config/password_config.json
        cfg_path = Path(settings.BASE_DIR) / "config" / "password_config.json"
        try:
            policy = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            # Fail closed with a reasonable default
            policy = {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digit": True,
                "require_special": True,
                "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                "forbidden_patterns": ["password", "123456", "qwerty", "abc123"],
                "max_repeat": 2
            }

        min_len = int(policy.get("min_length", 8))
        specials = str(policy.get("special_chars", "!@#$%^&*()_+-=[]{}|;:,.<>?"))
        max_repeat = int(policy.get("max_repeat", 2))

        if len(password) < min_len:
            self.add_error("new_password", f"Password must be at least {min_len} characters.")
        if policy.get("require_uppercase", True) and not re.search(r"[A-Z]", password):
            self.add_error("new_password", "Must include at least one uppercase letter.")
        if policy.get("require_lowercase", True) and not re.search(r"[a-z]", password):
            self.add_error("new_password", "Must include at least one lowercase letter.")
        if policy.get("require_digit", True) and not re.search(r"\d", password):
            self.add_error("new_password", "Must include at least one digit.")
        if policy.get("require_special", True) and not re.search("[" + re.escape(specials) + "]", password):
            self.add_error("new_password", f"Must include at least one special character ({specials}).")
        for pat in policy.get("forbidden_patterns", []):
            if pat and pat.lower() in password.lower():
                self.add_error("new_password", f"Password cannot contain '{pat}'.")
        # Limit repeated characters like "aaaa"
        reps = re.findall(r"(.)\1{"+str(max_repeat)+",}", password)
        if reps:
            self.add_error("new_password", f"Password cannot contain more than {max_repeat} repeated characters in a row.")