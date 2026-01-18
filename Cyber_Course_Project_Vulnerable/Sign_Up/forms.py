from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

from Cyber_Course_Project.password_policy import load_password_policy


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address."
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Required. Enter your first name."
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        help_text="Required. Enter your last name."
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Use the policy loader (single source of truth)
        self.policy = load_password_policy()
        self.fields["password1"].help_text = self.get_password_help_text()

    def get_password_help_text(self) -> str:
        p = self.policy
        requirements = [
            f"At least {p.min_length} characters long",
            f"At most {p.max_length} characters long",
        ]

        if p.require_uppercase:
            requirements.append(f"Contains at least {p.min_uppercase} uppercase letter(s)")
        if p.require_lowercase:
            requirements.append(f"Contains at least {p.min_lowercase} lowercase letter(s)")
        if p.require_digits:
            requirements.append(f"Contains at least {p.min_digits} digit(s)")
        if p.require_special_chars:
            requirements.append(f"Contains at least {p.min_special_chars} special character(s) ({p.special_chars})")

        if p.forbidden_patterns:
            requirements.append("Does not contain common patterns")

        requirements.append(f"No more than {p.max_repeated_chars} repeated characters in a row")

        return "Password must: " + ", ".join(requirements)

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if not password:
            return password

        p = self.policy
        errors: list[str] = []

        # Length
        if len(password) < p.min_length:
            errors.append(f"Password must be at least {p.min_length} characters long.")
        if len(password) > p.max_length:
            errors.append(f"Password must be no more than {p.max_length} characters long.")

        # Counts
        upper = len(re.findall(r"[A-Z]", password))
        lower = len(re.findall(r"[a-z]", password))
        digits = len(re.findall(r"\d", password))
        special = len(re.findall(r"[" + re.escape(p.special_chars) + r"]", password))

        if p.require_uppercase and upper < p.min_uppercase:
            errors.append(f"Password must contain at least {p.min_uppercase} uppercase letter(s).")
        if p.require_lowercase and lower < p.min_lowercase:
            errors.append(f"Password must contain at least {p.min_lowercase} lowercase letter(s).")
        if p.require_digits and digits < p.min_digits:
            errors.append(f"Password must contain at least {p.min_digits} digit(s).")
        if p.require_special_chars and special < p.min_special_chars:
            errors.append(f"Password must contain at least {p.min_special_chars} special character(s).")

        # Forbidden patterns
        for pattern in p.forbidden_patterns:
            if isinstance(pattern, str) and pattern and pattern.lower() in password.lower():
                errors.append(f"Password cannot contain common pattern: {pattern}")

        # Repeated characters (max allowed in a row = p.max_repeated_chars)
        # If max=2, forbid 3+ in a row => (.)\1{2,}
        if re.search(r"(.)\1{" + str(p.max_repeated_chars) + r",}", password):
            errors.append(
                f"Password cannot have more than {p.max_repeated_chars} repeated characters in a row."
            )

        if errors:
            raise ValidationError(errors)

        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.set_password(self.cleaned_data["password1"])
            user.save()
        return user