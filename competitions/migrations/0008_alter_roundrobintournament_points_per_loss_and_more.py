# Generated by Django 4.2.7 on 2024-04-11 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0007_remove_roundrobintournament_teams_per_match_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roundrobintournament',
            name='points_per_loss',
            field=models.DecimalField(decimal_places=10, default=0.0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='roundrobintournament',
            name='points_per_tie',
            field=models.DecimalField(decimal_places=10, default=1.0, max_digits=20),
        ),
        migrations.AlterField(
            model_name='roundrobintournament',
            name='points_per_win',
            field=models.DecimalField(decimal_places=10, default=3.0, max_digits=20),
        ),
    ]
