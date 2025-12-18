from django.db import models
from django.contrib.auth.models import User


class PasswordResetCode(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_codes")
	code = models.CharField(max_length=40, db_index=True)  # SHA-1 hex length
	created_at = models.DateTimeField(auto_now_add=True)
	used = models.BooleanField(default=False)

	def __str__(self):
		return f"ResetCode(user={self.user.username}, used={self.used})"

