# Generated by Django 5.1.2 on 2024-11-06 20:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assistants', '0008_openaiassistant_llm_provider_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='openaiassistant',
            name='is_archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='openaiassistant',
            name='version_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='openaiassistant',
            name='working_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='assistants.openaiassistant'),
        ),
    ]
