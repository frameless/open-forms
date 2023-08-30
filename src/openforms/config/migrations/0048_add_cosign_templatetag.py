# Generated by Django 3.2.19 on 2023-06-15 09:00

from django.db import migrations

from openforms.utils.migrations_utils.regex import add_cosign_info_templatetag


def add_cosign_template_tag_to_email_confirmation_template(apps, _):
    GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")

    config = GlobalConfiguration.objects.first()
    if not config:
        return

    template = config.confirmation_email_content
    updated_template = add_cosign_info_templatetag(template)

    config.confirmation_email_content = updated_template
    config.save()


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0047_globalconfiguration_enable_new_appointments"),
    ]

    operations = [
        migrations.RunPython(
            add_cosign_template_tag_to_email_confirmation_template,
            migrations.RunPython.noop,
        ),
    ]