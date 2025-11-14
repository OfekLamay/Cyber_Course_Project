from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    """
    Form for creating and editing customer records
    """
    
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'address', 'city', 'country', 'company_name', 
            'job_title', 'status', 'notes'
        ]
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'customer@example.com',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+972-50-1234567',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter full address',
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city',
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter country',
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name (optional)',
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job title (optional)',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional notes about the customer...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add required field indicators
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = True
                
        # Custom validation messages
        self.fields['email'].error_messages = {
            'invalid': 'Please enter a valid email address.',
            'unique': 'A customer with this email already exists.'
        }
        
        self.fields['phone_number'].error_messages = {
            'invalid': 'Please enter a valid phone number (e.g., +972-50-1234567).'
        }

    def clean_email(self):
        """Custom email validation"""
        email = self.cleaned_data.get('email')
        if email:
            # Check for existing customers with same email (excluding current instance)
            existing = Customer.objects.filter(email=email)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError("A customer with this email already exists.")
        
        return email

    def clean_phone_number(self):
        """Custom phone number validation"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove common separators for validation
            cleaned_phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            
            # Check if it starts with + and has correct length
            if not cleaned_phone.startswith('+') and not cleaned_phone.isdigit():
                raise forms.ValidationError("Phone number should contain only digits and optionally start with +")
                
        return phone

    def save(self, commit=True, user=None):
        """Save customer with creator information"""
        customer = super().save(commit=False)
        
        if user and not customer.pk:  # Only set creator for new customers
            customer.created_by = user
            
        if commit:
            customer.save()
            
        return customer