# Generated by Django 2.2.24 on 2021-07-20 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("zgw_consumers", "0012_auto_20210104_1039"),
    ]

    operations = [
        migrations.CreateModel(
            name="ObjectsAPIConfig",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "objecttype",
                    models.URLField(
                        blank=True,
                        help_text="Default URL of the ProductAanvraag OBJECTTYPE in the Objecttypes API. The objecttype should have the following three attributes: 1) submission_id; 2) type (the type of productaanvraag); 3) data (the submitted form data)",
                        max_length=1000,
                        verbose_name="objecttype",
                    ),
                ),
                (
                    "objecttype_version",
                    models.IntegerField(
                        blank=True,
                        help_text="Default version of the OBJECTTYPE in the Objecttypes API",
                        null=True,
                        verbose_name="objecttype version",
                    ),
                ),
                (
                    "productaanvraag_type",
                    models.CharField(
                        blank=True,
                        help_text="The type of ProductAanvraag",
                        max_length=255,
                        verbose_name="Productaanvraag type",
                    ),
                ),
                (
                    "objects_service",
                    models.OneToOneField(
                        limit_choices_to={"api_type": "orc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="zgw_consumers.Service",
                        verbose_name="Objects API",
                    ),
                ),
            ],
            options={
                "verbose_name": "Objects API configuration",
            },
        ),
    ]