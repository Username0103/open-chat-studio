# Generated by Django 4.2.15 on 2024-08-16 14:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pipelines', '0005_auto_20240802_0039'),
        ('experiments', '0088_experiment_use_processor_bot_voice'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='pipeline',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pipelines.pipeline', verbose_name='Pipeline'),
        ),
    ]
