# Generated by Django 5.1.2 on 2024-11-12 19:11

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assistants", "0008_openaiassistant_llm_provider_model"),
        ("custom_actions", "0001_initial"),
        ("experiments", "0101_experiment_llm_provider_model"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="customactionoperation",
            name="unique_experiment_custom_action_operation",
        ),
        migrations.RemoveConstraint(
            model_name="customactionoperation",
            name="unique_assistant_custom_action_operation",
        ),
        migrations.AddField(
            model_name="customactionoperation",
            name="_operation_schema",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="customactionoperation",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customactionoperation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="customactionoperation",
            name="working_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="versions",
                to="custom_actions.customactionoperation",
            ),
        ),
        migrations.AddConstraint(
            model_name="customactionoperation",
            constraint=models.UniqueConstraint(
                condition=models.Q(("experiment__isnull", False)),
                fields=("experiment", "custom_action", "operation_id"),
                name="unique_experiment_custom_action_operation",
            ),
        ),
        migrations.AddConstraint(
            model_name="customactionoperation",
            constraint=models.UniqueConstraint(
                condition=models.Q(("assistant__isnull", False)),
                fields=("assistant", "custom_action", "operation_id"),
                name="unique_assistant_custom_action_operation",
            ),
        ),
    ]
