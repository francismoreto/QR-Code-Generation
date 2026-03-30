# Generated migration for adding part name fields to VerificationLog

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_verificationlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='verificationlog',
            name='qr_part',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='verificationlog',
            name='user_part',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]
