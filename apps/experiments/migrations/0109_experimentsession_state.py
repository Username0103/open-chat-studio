# Generated by Django 5.1.2 on 2025-03-24 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0108_remove_participantdata_content_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='experimentsession',
            name='state',
            field=models.JSONField(default=dict),
        ),
    ]
