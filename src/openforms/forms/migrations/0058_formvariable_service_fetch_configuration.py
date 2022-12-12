# Generated by Django 3.2.16 on 2022-12-12 11:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("variables", "0001_add_service_fetch_configuration"),
        ("forms", "0057_alter_formvariable_data_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="formvariable",
            name="service_fetch_configuration",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="variables.servicefetchconfiguration",
                verbose_name="service fetch configuration",
            ),
        ),
    ]
