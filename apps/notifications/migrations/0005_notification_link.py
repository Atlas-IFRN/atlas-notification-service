from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_normalize_notification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='link',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
    ]
