# Generated by Django 2.2.16 on 2020-09-28 10:43

from django.db import migrations
import openforms.utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_form_backend'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='form',
            name='product',
        ),
        migrations.AddField(
            model_name='form',
            name='uuid',
            field=openforms.utils.fields.StringUUIDField(default=uuid.uuid4, unique=True),
        ),
        migrations.AddField(
            model_name='formdefinition',
            name='uuid',
            field=openforms.utils.fields.StringUUIDField(default=uuid.uuid4, unique=True),
        ),
        migrations.AddField(
            model_name='formstep',
            name='uuid',
            field=openforms.utils.fields.StringUUIDField(default=uuid.uuid4, unique=True),
        ),
        migrations.DeleteModel(
            name='Product',
        ),
    ]
