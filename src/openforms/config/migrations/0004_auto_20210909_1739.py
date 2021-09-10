# Generated by Django 2.2.24 on 2021-09-09 15:39

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0003_auto_20210907_0956"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="ask_privacy_consent",
            field=models.BooleanField(
                default=True,
                help_text="If enabled, the user will have to agree to the privacy policy before submitting a form.",
                verbose_name="ask privacy consent",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="privacy_policy_label",
            field=tinymce.models.HTMLField(
                blank=True,
                default="Ja, ik heb kennis genomen van het {% privacybeleid %} en geef uitdrukkelijk toestemming voor het verwerken van de door mij opgegeven gegevens.",
                help_text="The label of the checkbox that prompts the user to agree to the privacy policy.",
                verbose_name="privacy policy label",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="privacy_policy_url",
            field=models.URLField(
                blank=True,
                help_text="URL to the privacy policy",
                verbose_name="privacy policy URL",
            ),
        ),
    ]
