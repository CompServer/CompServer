# Generated by Django 4.2.7 on 2024-03-22 02:10

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0011_arena_color_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arena',
            name='color',
            field=colorfield.fields.ColorField(default=None, image_field=None, max_length=25, samples=None),
        ),
    ]