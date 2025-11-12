from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Customer(models.Model):
    """
    Customer model for storing client information
    """
    # Customer basic information
    first_name = models.CharField(
        max_length=50, 
        verbose_name="First Name",
        help_text="Customer's first name"
    )
    
    last_name = models.CharField(
        max_length=50, 
        verbose_name="Last Name",
        help_text="Customer's last name"
    )
    
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address",
        help_text="Customer's email address"
    )
    
    # Phone number with validation
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        verbose_name="Phone Number",
        help_text="Customer's phone number"
    )
    
    # Address information
    address = models.TextField(
        max_length=200,
        verbose_name="Address",
        help_text="Customer's full address"
    )
    
    city = models.CharField(
        max_length=50,
        verbose_name="City",
        help_text="Customer's city"
    )
    
    country = models.CharField(
        max_length=50,
        default="Israel",
        verbose_name="Country",
        help_text="Customer's country"
    )
    
    # Business information
    company_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Company Name",
        help_text="Customer's company (optional)"
    )
    
    job_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Job Title",
        help_text="Customer's job title (optional)"
    )
    
    # Customer status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('blocked', 'Blocked'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Status",
        help_text="Customer's current status"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Additional notes about the customer"
    )
    
    # System fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Created By",
        help_text="User who created this customer record"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        """Return customer's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_phone(self):
        """Format phone number for display"""
        if self.phone_number:
            # Simple formatting for display
            phone = self.phone_number.replace('+', '').replace('-', '').replace(' ', '')
            if len(phone) == 10:
                return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
            return self.phone_number
        return ""