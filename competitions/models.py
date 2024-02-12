from typing import Any
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.dispatch import receiver
from datetime import datetime
import pytz
from django.utils import timezone
from tzlocal import get_localzone
import random
import string


ACCESS_KEY_LENGTH = 10
def get_random_access_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=ACCESS_KEY_LENGTH))


# Class User
    # related: team_set (coached)
    # related: competition_set (judged)
    # related: tournament_set (judged)
    # related: profile


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # bio = models.TextField(blank=True)
    # profile_pic = models.ImageField()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Status(models.TextChoices):
    SETUP = "SETUP", _("Setup")  # for entries
    OPEN = "OPEN", _("Open")  # for judging
    CLOSED = "CLOSED", _("Closed")  # for judging
    COMPLETE = "COMPLETE", _("Complete")  # ready to show results
    ARCHIVED = "ARCHIVED", _("Archived")  # don't show to anyone (but data will be kept)

    @classmethod
    def max_length(cls):
        lengths = [len(member.value) for member in cls]
        return max(lengths)

class StatusField(models.CharField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs['max_length'] = Status.max_length()
        kwargs['choices'] = Status.choices
        kwargs['default'] = Status.SETUP
        super().__init__(*args, **kwargs)


class Organization(models.Model): # probably mostly schools but could also be community organizations
    name = models.CharField(max_length=257) # not unique because there could be schools with the same name just in different cities
    # logo = models.ImageField()
    # Attempt at an international-ambiguous addressing 
    # address_line1 = models.CharField(max_length=255) # Calle América 3
    # address_line2 = models.CharField(max_length=255) # Pozuelo de Alarcón 28224
    # address_line3 = models.CharField(max_length=255) # Madrid, Spain
    # related: teams

    def __str__(self) -> str:
        return str(self.name)  # + " (" + self.address_line3 + ")"
    

class Team(models.Model):
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE)
    coach = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)  # with special permissions to change info WRT the team
    # logo = models.ImageField()
    # related: competition_set, tournament_set, round1_matches, won_matches

    def __str__(self) -> str:
        return self.name + (_(" from ") + str(self.organization) if self.organization else "")
    
    def competed_in_at_least_

    def competed_in_at_least_one_tourney(self):
        for tourney in self.tournament_set:
            if tourney.status == "COMPLETE":
                return True
        return False

    class Meta:
        ordering = ['organization', 'name']
        unique_together = ['organization', 'name']


class Competition(models.Model):
    name = models.CharField(max_length=255, blank=True)
    status = StatusField()
    start_date = models.DateField()
    end_date = models.DateField()
    #? how much flexibility needed as far as shifting events to different days
    # address_line1 = models.CharField(max_length=255)
    # address_line2 = models.CharField(max_length=255)
    # address_line3 = models.CharField(max_length=255)
    teams = models.ManyToManyField(Team) # registered
    plenary_judges = models.ManyToManyField(User, blank=True)  # people entrusted to judge this competition as a whole: won't restrict them to a specific event
    access_key = models.CharField(max_length=ACCESS_KEY_LENGTH, default=get_random_access_key, blank=True, null=True)
    # For scheduling purposes, we need to be able to specify for this competition how many different (Event-specific) arenas are available and their capacity
    # related: tournament_set

    def currently_running(self):
        today = datetime.now().date()
        if self.start_date <= today and self.end_date >= today:
            return True
        else:
            return False

    #checks if the competition has ended (true)
    #checks if the competition hasn't ended (false)

    def __str__(self) -> str:
        # dwheadon: check if the name is unique for this year, otherwise add the month/day as well
        if Competition.objects.filter(name=self.name).count() > 1:
            if Competition.objects.filter(name=self.name, start_date__year=self.start_date.year).count() > 1:
                if Competition.objects.filter(name=self.name, start_date__year=self.start_date.year, start_date__month=self.start_date.month).count() > 1:
                    # if you have two on the same day, good luck
                    return self.name + " " + str(self.start_date.month)+ " " + str(self.start_date.day) + ", " + str(self.start_date.year) # RoboMed June, 2023
                else:
                    return self.name + " " + str(self.start_date.month) + ", " + str(self.start_date.year) # RoboMed June, 2023
            else:
                return self.name + " " + str(self.start_date.year) # RoboMed 2023
        else:
            return self.name

    @property
    def is_viewable(self) -> bool:
        """Whether the object should show up on the website."""
        return self.status in [Status.OPEN, Status.COMPLETE, Status.CLOSED]

    @property
    def is_judgable(self) -> bool:
        """Whether judging for this comptetation should be allowed."""
        return self.status == Status.OPEN
    
    @property
    def is_complete(self) -> bool:
        return self.status == Status.COMPLETE

    @property
    def is_closed(self) -> bool:
        return self.status == Status.CLOSED
    
    @property
    def is_archived(self) -> bool:
        return self.status == Status.ARCHIVED
    
    @property
    def is_in_setup(self) -> bool:
        return self.status == Status.SETUP
    
    class Meta:
        ordering = ['-start_date', 'name']
        unique_together = ['start_date', 'name'] # probably won't have 2 in the same year but you could have a quarterly / monthly / even weekly competition


# class ScoreUnits(models.TextChoices):
#     PLACE = "PLA", _("Place")
#     SECONDS = "SEC", _("Seconds")
#     GOALS = "GOL", _("Goals")
#     POINTS = "PNT", _("Points")

#     @classmethod
#     def max_length(cls):
#         lengths = [len(member.value) for member in cls]
#         return max(lengths)


# class ScoreUnitsField(models.CharField):
#     def __init__(self, *args: Any, **kwargs: Any) -> None:
#         kwargs['max_length'] = ScoreUnits.max_length()
#         kwargs['choices'] = ScoreUnits.choices
#         kwargs['default'] = ScoreUnits.POINTS
#         super().__init__(*args, **kwargs)


class Event(models.Model):
    name = models.CharField(max_length=255, unique=True)  # sumo bots, speed race, etc.
    # score_units = ScoreUnitsField() # initially just assume scores are place values (1st, 2nd, 3rd, etc.)
    # high_score_advances = models.BooleanField(default=True) # with seconds, low scores will usually advance (unless it's a "how long can you last" situation)
    # related: tournament_set

    def __str__(self) -> str:
        return str(self.name)


# dwheadon: can we force this to be abstract (non-instantiable)?
class AbstractTournament(models.Model):
    status = StatusField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tournament_set") # besides helpfing to identify this tournament this will change how teams advance (high or low score)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="tournament_set")
    points = models.DecimalField(max_digits=20, decimal_places=10) # for winner # dwheadon: is 10 digits / decimals enough / too much?
    # interpolate_points = models.BooleanField(default=False) # otherwise winner takes all: RoboMed doesn't need this but it could be generally useful
    teams = models.ManyToManyField(Team, related_name="tournament_set")
    judges = models.ManyToManyField(User, blank=True, related_name="tournament_set")  # people entrusted to judge this tournament alone (as opposed to plenary judges)
    # These Event-related things might depend on the competition: speed race with 1 v 1 at this competition but speed race with 4 v 4 at another (both are the same event)
    # max_teams_per_match = models.SmallIntegerField(default=2)
    # max_teams_to_advance = models.SmallIntegerField(default=1)
    # teams_to_advance_rounds_up = models.BooleanField() # in a 4max/2adv situation if a match only has enough for say 3 competitors, do we advance two (round up) or 1 (round down)
    # tied_teams_all_advance = models.BooleanField()
    # dwheadon: what about tie_breakers? should we have a field for that?
    # related: match_set, ranking_set

    def __str__(self) -> str:
        return self.event.name + _(" tournament @ ") + str(self.competition) # SumoBot tournament at RoboMed 2023
    
    @property
    def is_viewable(self) -> bool:
        """Whether the object should show up on the website."""
        return self.status in [Status.OPEN, Status.COMPLETE, Status.CLOSED]

    @property
    def is_judgable(self) -> bool:
        """Whether judging for this comptetation should be allowed."""
        return self.status == Status.OPEN
    
    @property
    def is_complete(self) -> bool:
        return self.status == Status.COMPLETE

    @property
    def is_closed(self) -> bool:
        return self.status == Status.CLOSED
    
    @property
    def is_archived(self) -> bool:
        return self.status == Status.ARCHIVED
    
    @property
    def is_in_setup(self) -> bool:
        return self.status == Status.SETUP

    class Meta:
        ordering = ['competition', 'event']

class Ranking(models.Model):
    """ These will determine the auto-layout of the brackets """
    tournament = models.ForeignKey(AbstractTournament, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField()

    def __str__(self) -> str:
        return str(self.rank) + ") " + str(self.team.name) + " in " + str(self.tournament)

    class Meta:
        ordering = ['tournament', 'rank']
        unique_together = [['tournament', 'team']] 
        # unique_together += ['tournament', 'rank'] # NCAA has 4 teams with a #1 seed


class SingleEliminationTournament(AbstractTournament):
    ''' Elimination style with brackets (last man standing) 
        Requires seedings determined by prior RoundRobin or expert input
        Seeding (ranking) is important because you want the last match to be close, not a total blowout
        Winner take all situation (1st place is really the only position that's established)
    '''
    # interpolated: winner (of the top-level match)


# class DoubleEliminationTournament(AbstractTournament):
#     ''' Has a "looser's" bracket
#         Everybody plays at least 2 matches
#         Winner of loser's bracket gets to play for 2nd place?
#     '''
#     # interpolated: 1st place (winner of the top-level "winner's" bracket)
#     # interpolated: 2nd place (winner of the top-level "loser's" bracket)


# class MultilevelTournament(AbstractTournament):
#     # prerequisite: have to have a ranking to begin with
#     ''' Keep moving down each time you loose
#         Don't realy know how you determine who you play next when you loose
#         Assuming the rankings were perfect, this is how it would play out?
#         1/8
#             1/4 (1W0L)
#             2/3 (1W0L)
#         4/5
#                     1---(3W0L)
#                 1/2 (2W0L)
#                         2---(4W1L)
#                     2/5 (2W1L)
#                     2/3 (2W1L)
#                     3/5 (2W1L)
#                             3---(4W2L)
#                         3/4 (3W2L)
#                                 4---(4W3L)
#                             4/5 (3W3L)
#                                 5---(3W4L)
#                         5/6 (2W3L)
#                             6---(2W4L)
#                 3/4 (1W1L)
#                     4/7 (1W2L)
#                     4/6 (1W2L)
#                     6/7 (1W2L)
#                         7---(1W4L)
#                 5/6 (1W1L)
#                 7/8 (0W2L)
#                     8---(0W3L)
#         2/7
#             5/8 (0W1L)
#             6/7 (0W1L)
#         3/6
#     '''
#     # interpolated: full rankings (sequence of wins / losses)


# class RoundRobinTournament(AbstractTournament):
#     ''' Everyone plays everyone else (most points / wins, wins) 
#         Can be used to establish rankings for an Elimination
#         This is often used for league play (not necessarily a tournament)
#     '''
#     # points_per_win: 3 for World Cup group round
#     # points_per_tie: 1 for World Cup group round
#     # points_per_loss: probably always 0
#     # accumulation: sum of all points (e.g. goals), sum of match points (e.g. 2 for win, 1 for tie, 0 for loss)
#     # interpolated: rull rankings (order of points)


class Match(models.Model):
    ''' Could be a one-off preliminary match or part of a larger tournament '''
    tournament = models.ForeignKey(AbstractTournament, models.CASCADE, blank=True, null=True)
    # Note: admin doesn't enforce the starting teams to be registered for this tournament
    starting_teams = models.ManyToManyField(Team, related_name="round1_matches", blank=True) # Only used for round1 matches, all others use the previous matches. Usually just 2 but could be more (speed race)
    # Note: admin doesn't restrict to previous matches from this tournament
    prev_matches = models.ManyToManyField('self', symmetrical=False, blank=True, related_name="next_matches") # Except for round1 of a tournament (or one-off preliminary matches), advancers from the previous matches will be the competitors for this match
    # Note: admin doesn't restrict advancers to be competitors for this match
    advancers = models.ManyToManyField(Team, related_name="won_matches", blank=True) # usually 1 but could be more (e.g. time trials)
    time = models.DateTimeField() # that it's scheduled for
    str_recursive_level = 0

    def currently_running(self):
        now = timezone.localtime(timezone.now())
        dates = datetime.now()
        datetime = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        timezone = get_localzone()
        one_date = self.time
        another_date = utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)
        third_date = local_dt.astimezone(pytz.utc)
        something = datetime.now()
        now = pytz.utc.localize(something)
        if self.time >= now:
            return True
        else: 
            return False

    def __str__(self) -> str:
        self.__class__.str_recursive_level += 1
        competitors = []
        if self.starting_teams.exists():
            competitors += [(("[" + team.name + "]") if team in self.advancers.all() else team.name) for team in self.starting_teams.all()]
        if self.prev_matches.exists():
            for prev_match in self.prev_matches.all():
                prior_match_advancing_teams = prev_match.advancers.all()
                if prev_match.advancers.exists():
                    competitors += [(("[" + team.name + "]") if team in self.advancers.all() else team.name) for team in prev_match.advancers.all()]
                else:
                    competitors += ["Winner of (" + str(prev_match) + ")"]
        self.__class__.str_recursive_level -= 1
        res = _(" vs ").join(competitors) # Battlebots vs Byters
        if self.__class__.str_recursive_level == 0:
            return res + _(" in ") + str(self.tournament) # Battlebots vs Byters in SumoBot tournament @ RoboMed 2023
        else: 
            return res # if part of another match we don't want to repeat the tournament

    class Meta:
        ordering = ['tournament']
        verbose_name_plural = _('Matches')
