from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0006_auditlog'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(
                fields=['-created_at'],
                name='notif_audit_created_idx',
            ),
        ),
    ]
