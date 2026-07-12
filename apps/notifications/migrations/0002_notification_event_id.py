from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='event_id',
            field=models.UUIDField(blank=True, db_index=True, null=True, unique=True),
        ),
    ]
