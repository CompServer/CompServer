# Generated by Django 4.2.7 on 2024-05-23 21:30

import competitions.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AbstractTournament',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teams_per_match', models.PositiveSmallIntegerField(default=2)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('status', competitions.models.StatusField(choices=[('SETUP', 'Setup'), ('OPEN', 'Open'), ('CLOSED', 'Closed'), ('COMPLETE', 'Complete'), ('ARCHIVED', 'Archived')], default='SETUP', max_length=8)),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('points', models.DecimalField(blank=True, decimal_places=10, max_digits=20, null=True)),
                ('max_teams_to_advance', models.SmallIntegerField(default=1)),
            ],
            options={
                'ordering': ['competition', 'event'],
            },
        ),
        migrations.CreateModel(
            name='Arena',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100)),
                ('capacity', models.PositiveSmallIntegerField(default=1)),
                ('is_available', models.BooleanField(default=True)),
                ('color', competitions.models.ColorField(default='#CBCBCB', image_field=None, max_length=25, samples=None)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='arenas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'owner')},
            },
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(blank=True, null=True)),
                ('_cached_str', models.TextField(blank=True, null=True)),
                ('round_num', models.PositiveIntegerField(default=1)),
            ],
            options={
                'verbose_name_plural': 'Matches',
                'ordering': ['tournament'],
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=257)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organizations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'owner')},
            },
        ),
        migrations.CreateModel(
            name='SiteConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('icon', models.CharField(blank=True, max_length=255, null=True)),
                ('style_sheet', models.CharField(blank=True, max_length=255, null=True)),
                ('use_demo_mode', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Sport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'owner')},
            },
        ),
        migrations.CreateModel(
            name='RoundRobinTournament',
            fields=[
                ('abstracttournament_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='competitions.abstracttournament')),
                ('matches_per_team', models.PositiveSmallIntegerField()),
                ('points_per_win', models.DecimalField(decimal_places=10, default=3.0, max_digits=20)),
                ('points_per_tie', models.DecimalField(decimal_places=10, default=1.0, max_digits=20)),
                ('points_per_loss', models.DecimalField(decimal_places=10, default=0.0, max_digits=20)),
            ],
            options={
                'verbose_name': 'Preliminary Tournament (Round Robin)',
                'verbose_name_plural': 'Preliminary Tournaments (Round Robin)',
            },
            bases=('competitions.abstracttournament',),
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('coach', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='competitions.organization')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teams', to=settings.AUTH_USER_MODEL)),
                ('sport', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='competitions.sport')),
            ],
            options={
                'ordering': ['sport', 'organization', 'name'],
                'unique_together': {('organization', 'name', 'owner')},
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True)),
                ('profile_pic', models.ImageField(default='static/default_pfp.jpg', upload_to='profile_pics')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PointsEarned',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(null=True)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='points_earned_set', to='competitions.match')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='points_earned_set', to='competitions.team')),
            ],
        ),
        migrations.AddField(
            model_name='match',
            name='advancers',
            field=models.ManyToManyField(blank=True, related_name='won_matches', to='competitions.team'),
        ),
        migrations.AddField(
            model_name='match',
            name='arena',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='match_set', to='competitions.arena'),
        ),
        migrations.AddField(
            model_name='match',
            name='prev_matches',
            field=models.ManyToManyField(blank=True, related_name='next_matches', to='competitions.match'),
        ),
        migrations.AddField(
            model_name='match',
            name='starting_teams',
            field=models.ManyToManyField(blank=True, related_name='round1_matches', to='competitions.team'),
        ),
        migrations.AddField(
            model_name='match',
            name='tournament',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='match_set', to='competitions.abstracttournament'),
        ),
        migrations.CreateModel(
            name='HistoricalMatch',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('time', models.DateTimeField(blank=True, null=True)),
                ('_cached_str', models.TextField(blank=True, null=True)),
                ('round_num', models.PositiveIntegerField(default=1)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('arena', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='competitions.arena')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('tournament', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='competitions.abstracttournament')),
            ],
            options={
                'verbose_name': 'historical match',
                'verbose_name_plural': 'historical Matches',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('match_time', models.DurationField()),
                ('color', competitions.models.ColorField(default='#CBCBCB', image_field=None, max_length=25, samples=None)),
                ('use_units', models.BooleanField(default=False)),
                ('units', models.CharField(default='point', max_length=25)),
                ('units_verbose', models.CharField(default='points', max_length=26)),
                ('use_higher_score', models.BooleanField(default=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to=settings.AUTH_USER_MODEL)),
                ('sport', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='competitions.sport')),
            ],
            options={
                'ordering': ['sport', 'name', 'owner'],
            },
        ),
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
                ('status', competitions.models.StatusField(choices=[('SETUP', 'Setup'), ('OPEN', 'Open'), ('CLOSED', 'Closed'), ('COMPLETE', 'Complete'), ('ARCHIVED', 'Archived')], default='SETUP', max_length=8)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('access_key', models.CharField(blank=True, default=competitions.models.get_random_access_key, max_length=10, null=True)),
                ('arenas', models.ManyToManyField(to='competitions.arena')),
                ('host', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='competitions.organization')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competitions', to=settings.AUTH_USER_MODEL)),
                ('plenary_judges', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
                ('sport', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='competitions.sport')),
                ('teams', models.ManyToManyField(blank=True, to='competitions.team')),
            ],
            options={
                'ordering': ['-start_date', 'name'],
                'unique_together': {('start_date', 'name', 'owner')},
            },
        ),
        migrations.AddField(
            model_name='abstracttournament',
            name='competition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tournament_set', to='competitions.competition'),
        ),
        migrations.AddField(
            model_name='abstracttournament',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tournament_set', to='competitions.event'),
        ),
        migrations.AddField(
            model_name='abstracttournament',
            name='judges',
            field=models.ManyToManyField(blank=True, related_name='tournament_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='abstracttournament',
            name='teams',
            field=models.ManyToManyField(related_name='tournament_set', to='competitions.team'),
        ),
        migrations.CreateModel(
            name='SingleEliminationTournament',
            fields=[
                ('abstracttournament_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='competitions.abstracttournament')),
                ('prev_tournament', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='competitions.roundrobintournament')),
            ],
            bases=('competitions.abstracttournament',),
        ),
        migrations.CreateModel(
            name='Ranking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveSmallIntegerField()),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competitions.team')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ranking_set', to='competitions.abstracttournament')),
            ],
            options={
                'ordering': ['tournament', 'rank'],
                'unique_together': {('tournament', 'team')},
            },
        ),
    ]
