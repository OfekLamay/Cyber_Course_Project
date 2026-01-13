from django.contrib import admin
from .models import PasswordResetCode

@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "created_at", "used")
    search_fields = ("user__username", "user__email", "code")
    list_filter = ("used", "created_at")