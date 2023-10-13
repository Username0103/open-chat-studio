# Generated by Django 4.2 on 2023-10-11 15:18
import os, json
from django.db import migrations


def load_language_code(apps, schema_editor):
    SyntheticVoice = apps.get_model("experiments", "SyntheticVoice")
    voice_data = {}
    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, "preload_data/aws_voices.json")

    with open(file_path, "r") as json_file:
        voice_data = json.load(json_file)["voices"]

    voices_created = 0
    voices_edited = 0
    for voice in voice_data:
        _, created = SyntheticVoice.objects.update_or_create(
            name=voice["name"],
            language=voice["language"],
            gender=voice["gender"],
            neural=voice["neural"],
            service=voice["service"],
            defaults={
                "language_code": voice["language_code"],
            }
        )

        if created:
            voices_created += 1
        else:
            voices_edited += 1
    print(f"{voices_created} synthetic voices were created")
    print(f"{voices_edited} synthetic voices were edited")

def drop_language_code(apps, schema_editor):
    SyntheticVoice = apps.get_model("experiments", "SyntheticVoice")
    SyntheticVoice.objects.all().update(language_code="<undef>")


class Migration(migrations.Migration):
    dependencies = [
        ("experiments", "0038_alter_syntheticvoice_unique_together_and_more"),
    ]

    operations = [migrations.RunPython(load_language_code, drop_language_code)]

