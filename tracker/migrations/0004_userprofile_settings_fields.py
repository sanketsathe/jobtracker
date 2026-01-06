from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0003_userprofile_followup_application_updates"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="ui_density",
            field=models.CharField(
                choices=[("COMFORTABLE", "Comfortable"), ("COMPACT", "Compact")],
                default="COMFORTABLE",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="theme_preference",
            field=models.CharField(
                choices=[("SYSTEM", "System"), ("LIGHT", "Light"), ("DARK", "Dark")],
                default="SYSTEM",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="reduce_motion",
            field=models.BooleanField(default=False),
        ),
    ]
