# Generated by Django 4.2.7 on 2024-03-28 18:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='match',
            name='round',
        ),
    ]