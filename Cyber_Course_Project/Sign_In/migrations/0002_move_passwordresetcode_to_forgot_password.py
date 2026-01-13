from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Sign_In", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Remove the model from the Sign_In app's state, but keep the DB table.
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(
                    name="PasswordResetCode",
                ),
            ],
        ),
    ]
