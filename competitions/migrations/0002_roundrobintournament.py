# Generated by Django 4.2.6 on 2024-03-01 03:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoundRobinTournament',
            fields=[
                ('abstracttournament_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='competitions.abstracttournament')),
                ('num_matches', models.PositiveSmallIntegerField()),
            ],
            bases=('competitions.abstracttournament',),
        ),
    ]