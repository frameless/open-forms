# Generated by Django 2.2.20 on 2021-05-10 09:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("zgw_consumers", "0012_auto_20210104_1039"),
    ]

    operations = [
        migrations.CreateModel(
            name="ZgwConfig",
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
                    "zaaktype",
                    models.URLField(
                        help_text="Default URL of the ZAAKTYPE in Catalogi API",
                        max_length=1000,
                    ),
                ),
                (
                    "informatieobjecttype",
                    models.URLField(
                        help_text="Default URL of the INFORMATIEOBJECTTYPE in Catalogi API",
                        max_length=1000,
                    ),
                ),
                (
                    "organisatie_rsin",
                    models.CharField(
                        help_text="Default RSIN of organization, which creates the ZAAK",
                        max_length=9,
                    ),
                ),
                (
                    "drc_service",
                    models.OneToOneField(
                        limit_choices_to={"api_type": "drc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="zgw_drc_config",
                        to="zgw_consumers.Service",
                    ),
                ),
                (
                    "zrc_service",
                    models.OneToOneField(
                        limit_choices_to={"api_type": "zrc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="zgw_zrc_config",
                        to="zgw_consumers.Service",
                    ),
                ),
                (
                    "ztc_service",
                    models.OneToOneField(
                        limit_choices_to={"api_type": "ztc"},
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="zgw_ztc_config",
                        to="zgw_consumers.Service",
                    ),
                ),
            ],
            options={
                "verbose_name": "ZGW Configuration",
            },
        ),
    ]