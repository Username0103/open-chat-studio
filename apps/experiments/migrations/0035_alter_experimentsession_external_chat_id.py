# Generated by Django 4.2 on 2023-10-11 09:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0034_merge_channel_session_with_experiment_session"),
    ]

    operations = [
        migrations.AlterField(
            model_name="experimentsession",
            name="external_chat_id",
            field=models.CharField(default=""),
            preserve_default=False,
        ),
    ]
