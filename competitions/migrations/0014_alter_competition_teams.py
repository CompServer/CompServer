# Generated by Django 4.2.7 on 2024-02-15 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0013_alter_team_options_competition_sport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competition',
            name='teams',
            field=models.ManyToManyField(blank=True, to='competitions.team'),
        ),
    ]
