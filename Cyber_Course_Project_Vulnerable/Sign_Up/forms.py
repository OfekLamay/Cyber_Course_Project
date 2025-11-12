from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json
import os
import re
import hashlib
import hmac
from django.conf import settings

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
        # Load password policy from config
        self.password_config = self.load_password_config()
        
        # Update help text for password fields
        self.fields['password1'].help_text = self.get_password_help_text()
        
    def load_password_config(self):
        """Load password configuration from JSON file"""
        try:
            config_path = os.path.join(settings.BASE_DIR, 'config', 'password_config.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default config if file not found
            return {
                "password_policy": {
                    "min_length": 8,
                    "require_uppercase": True,
                    "require_lowercase": True,
                    "require_digits": True,
                    "require_special_chars": True,
                    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                }
            }
    
    def get_password_help_text(self):
        """Generate help text based on password policy"""
        policy = self.password_config.get('password_policy', {})
        requirements = [
            f"At least {policy.get('min_length', 8)} characters long",
        ]
        
        if policy.get('require_uppercase'):
            requirements.append("Contains uppercase letter")
        if policy.get('require_lowercase'):
            requirements.append("Contains lowercase letter")
        if policy.get('require_digits'):
            requirements.append("Contains at least one digit")
        if policy.get('require_special_chars'):
            requirements.append(f"Contains special character ({policy.get('special_chars', '!@#$%^&*')})")
            
        return "Password must: " + ", ".join(requirements)

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_password1(self):
        """Validate password according to policy"""
        password = self.cleaned_data.get('password1')
        if not password:
            return password
            
        policy = self.password_config.get('password_policy', {})
        errors = []

        # Check minimum length
        min_length = policy.get('min_length', 8)
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long.")

        # Check maximum length
        max_length = policy.get('max_length', 128)
        if len(password) > max_length:
            errors.append(f"Password must be no more than {max_length} characters long.")

        # Check uppercase requirement
        if policy.get('require_uppercase') and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter.")

        # Check lowercase requirement
        if policy.get('require_lowercase') and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter.")

        # Check digits requirement
        if policy.get('require_digits') and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one digit.")

        # Check special characters requirement
        if policy.get('require_special_chars'):
            special_chars = policy.get('special_chars', '!@#$%^&*()_+-=[]{}|;:,.<>?')
            if not re.search(f'[{re.escape(special_chars)}]', password):
                errors.append(f"Password must contain at least one special character: {special_chars}")

        # Check forbidden patterns
        forbidden_patterns = policy.get('forbidden_patterns', [])
        for pattern in forbidden_patterns:
            if pattern.lower() in password.lower():
                errors.append(f"Password cannot contain common pattern: {pattern}")

        # Check repeated characters
        max_repeated = policy.get('max_repeated_chars', 2)
        for i in range(len(password) - max_repeated):
            if len(set(password[i:i+max_repeated+1])) == 1:
                errors.append(f"Password cannot have more than {max_repeated} repeated characters in a row.")

        if errors:
            raise ValidationError(errors)
            
        return password

    def save(self, commit=True):
        """Save user with Django's built-in password hashing (includes PBKDF2 + Salt)"""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            # Use Django's built-in password hashing (PBKDF2 + Salt + HMAC)
            # This already implements HMAC + Salt as required
            user.set_password(self.cleaned_data["password1"])
            user.save()
        return user