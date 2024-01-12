# Generated by Django 3.2.23 on 2023-12-21 16:03

from django.db import migrations

from openforms.forms.fd_translations_converter import process_component_tree


def migrate_fd_translations(apps, _):
    FormDefinition = apps.get_model("forms", "FormDefinition")

    for form_definition in FormDefinition.objects.iterator():
        has_translations = any(
            bool(translations)
            for translations in form_definition.component_translations.values()
        )
        if not has_translations:
            continue

        process_component_tree(
            components=form_definition.configuration["components"],
            translations_store=form_definition.component_translations,
        )
        form_definition.save(update_fields=["configuration"])


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0101_update_action_property"),
    ]

    operations = [
        migrations.RunPython(migrate_fd_translations, migrations.RunPython.noop),
    ]