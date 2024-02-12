# Generated by Django 4.2.7 on 2024-02-06 19:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0006_alter_match_prev_matches'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='prev_matches',
            field=models.ManyToManyField(blank=True, related_name='next_matches', to='competitions.match'),
        ),
    ]