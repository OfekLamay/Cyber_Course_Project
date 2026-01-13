from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import PasswordResetCode

class ResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", email="u1@example.com", password="P@ssw0rd!")

    def test_verify_requires_valid_code(self):
        PasswordResetCode.objects.create(user=self.user, code="x"*40, created_at=timezone.now(), used=False)
        r = self.client.post(reverse("Forgot_Password:verify_code"), {"email": "u1@example.com", "code": "x"*40})
        self.assertEqual(r.status_code, 302)