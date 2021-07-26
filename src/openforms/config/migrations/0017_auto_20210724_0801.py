# Generated by Django 2.2.24 on 2021-07-24 06:01

from django.db import migrations, models
import functools
import openforms.utils.translations


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0016_load_default_cookiegroups"),
    ]

    operations = [
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_begin_text",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default, *("Begin form",), **{}
                ),
                help_text="The text that will be displayed at the start of the form to indicate the user can begin to fill in the form",
                max_length=50,
                verbose_name="begin text",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_change_text",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default, *("Change",), **{}
                ),
                help_text="The text that will be displayed in the overview page to change a certain step",
                max_length=50,
                verbose_name="change text",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_confirm_text",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default, *("Confirm",), **{}
                ),
                help_text="The text that will be displayed in the overview page to confirm the form is filled in correctly",
                max_length=50,
                verbose_name="confirm text",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_previous_text",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default, *("Previous page",), **{}
                ),
                help_text="The text that will be displayed in the overview page to go to the previous step",
                max_length=50,
                verbose_name="previous text",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_step_next_text",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default, *("Next",), **{}
                ),
                help_text="The text that will be displayed in the form step to go to the next step",
                max_length=50,
                verbose_name="step next text",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_step_previous_text",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default, *("Previous page",), **{}
                ),
                help_text="The text that will be displayed in the form step to go to the previous step",
                max_length=50,
                verbose_name="step previous text",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="form_step_save_text",
            field=models.CharField(
                default=functools.partial(
                    openforms.utils.translations.get_default,
                    *("Save current information",),
                    **{}
                ),
                help_text="The text that will be displayed in the form step to save the current information",
                max_length=50,
                verbose_name="step save text",
            ),
        ),
        migrations.AlterField(
            model_name="globalconfiguration",
            name="piwik_url",
            field=models.CharField(
                blank=True,
                help_text="The base URL of your Piwik server, e.g. 'piwik.example.com'.",
                max_length=255,
                verbose_name="Piwik server URL",
            ),
        ),
    ]
