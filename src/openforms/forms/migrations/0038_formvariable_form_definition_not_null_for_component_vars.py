# Generated by Django 3.2.14 on 2022-07-29 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0037_remove_invalid_component_vars"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="formvariable",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(
                            ("form_definition__isnull", True),
                            models.Q(("source", "component"), _negated=True),
                        ),
                        ("form_definition__isnull", False),
                        _connector="OR",
                    )
                ),
                name="form_definition_not_null_for_component_vars",
            ),
        ),
    ]