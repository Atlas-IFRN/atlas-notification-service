from django.db import migrations

# Normaliza os valores de `type` gravados antes da mudança do enum
# (0003_alter_notification_type), que passou os tipos para minúsculo.
# As linhas antigas mantêm o valor em maiúsculo; aqui convertemos para o
# novo vocabulário. EVALUATION (removido) vira `track`, que é a origem
# equivalente (avaliação de desafio).
TYPE_MAP = {
    'SYSTEM': 'system',
    'SCHOLARSHIP': 'scholarship',
    'EVALUATION': 'track',
}


def normalize_types(apps, schema_editor):
    Notification = apps.get_model('notifications', 'Notification')
    for old, new in TYPE_MAP.items():
        Notification.objects.filter(type=old).update(type=new)


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_alter_notification_type'),
    ]

    operations = [
        # Normalização de dados sem reverso (o vocabulário antigo em maiúsculo
        # não existe mais no enum).
        migrations.RunPython(normalize_types, migrations.RunPython.noop),
    ]
