# Generated by Django 3.2.23 on 2024-01-18 14:09

from django.db import migrations

from openforms.forms.migration_operations import ConvertComponentsOperation


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0103_fix_component_problems"),
    ]

    operations = [
        ConvertComponentsOperation(
            "datetime", "prevent_datetime_components_from_emptying_invalid_values"
        ),
    ]
