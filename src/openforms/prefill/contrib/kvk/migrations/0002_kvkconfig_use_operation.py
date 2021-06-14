# Generated by Django 2.2.20 on 2021-06-14 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("prefill_kvk", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="kvkconfig",
            name="use_operation",
            field=models.CharField(
                choices=[
                    ("Companies_GetCompaniesExtendedV2", "Production"),
                    ("CompaniesTest_GetCompaniesExtendedV2", "Development"),
                ],
                default="Companies_GetCompaniesExtendedV2",
                help_text="The development API uses different paths/operations",
                max_length=255,
                verbose_name="OAS operation",
            ),
        ),
    ]
