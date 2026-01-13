# Move PasswordResetCode model state to Forgot_Password

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("Sign_In", "0002_move_passwordresetcode_to_forgot_password"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Keep the existing DB table created by Sign_In.0001_initial.
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="PasswordResetCode",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("code", models.CharField(db_index=True, max_length=40)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("used", models.BooleanField(default=False)),
                        (
                            "user",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="password_reset_codes",
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                    ],
                    options={
                        "db_table": "Sign_In_passwordresetcode",
                    },
                ),
            ],
        ),
    ]
