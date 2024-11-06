import datetime
import math
import random
import string
from typing import Any, ClassVar, List

from django.contrib.auth.models import User
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.db.models import CharField, signals
from django.db.models.fields.files import ImageField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from config.settings import DEMO

from .utils_colorfield import get_image_file_background_color
from .validators import (
    color_hex_validator,
    color_hexa_validator,
    color_rgb_validator,
    color_rgba_validator,
)
from .widgets import ColorWidget

ACCESS_KEY_LENGTH = 10
# ^ should be in settings?
# yes

def get_random_access_key():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=ACCESS_KEY_LENGTH))

# Class User
    # related: team_set (coached)
    # related: competition_set (judged)
    # related: tournament_set (judged)
    # related: profile

# https://github.com/h3/django-colorfield/blob/master/colorfield/fields.py




VALIDATORS_PER_FORMAT = {
    "hex": color_hex_validator,
    "hexa": color_hexa_validator,
    "rgb": color_rgb_validator,
    "rgba": color_rgba_validator,
}

DEFAULT_PER_FORMAT = {
    "hex": "#FFFFFF",
    "hexa": "#FFFFFFFF",
    "rgb": "rgb(255, 255, 255)",
    "rgba": "rgba(255, 255, 255, 1)",
}

class ColorField(CharField):
    default_validators = []

    def __init__(self, *args, **kwargs):
        # works like Django choices, but does not restrict input to the given choices
        self.samples = kwargs.pop("samples", None)
        self.format = kwargs.pop("format", "hex").lower()
        if self.format not in ["hex", "hexa", "rgb", "rgba"]:
            raise ValueError(f"Unsupported color format: {self.format}")
        self.default_validators = [VALIDATORS_PER_FORMAT[self.format]]

        self.image_field = kwargs.pop("image_field", None)
        if self.image_field:
            kwargs.setdefault("blank", True)

        kwargs.setdefault("max_length", 25)
        if kwargs.get("null"):
            kwargs.setdefault("blank", True)
            kwargs.setdefault("default", None)
        elif kwargs.get("blank"):
            kwargs.setdefault("default", "")
        else:
            kwargs.setdefault("default", DEFAULT_PER_FORMAT[self.format])
        super().__init__(*args, **kwargs)

        if self.choices and self.samples:
            raise ImproperlyConfigured(
                "Invalid options: 'choices' and 'samples' are mutually exclusive, "
                "you can set only one of the two for a ColorField instance."
            )

    def formfield(self, **kwargs):
        palette = []
        if self.choices:
            choices = self.get_choices(include_blank=False)
            palette = [choice[0] for choice in choices]
        elif self.samples:
            palette = [choice[0] for choice in self.samples]
        kwargs["widget"] = ColorWidget(
            attrs={
                "default": self.get_default(),
                "format": self.format,
                "palette": palette,
                # # TODO: in case choices is defined,
                # # this will be used to hide the widget color spectrum
                # 'palette_choices_only': bool(self.choices),
            }
        )
        return super().formfield(**kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        if cls._meta.abstract:
            return
        if self.image_field:
            signals.post_save.connect(self._update_from_image_field, sender=cls)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["samples"] = self.samples
        kwargs["image_field"] = self.image_field
        return name, path, args, kwargs

    def _get_image_field_color(self, instance):
        color = ""
        image_file = getattr(instance, self.image_field)
        if image_file:
            with image_file.open() as _:
                color = get_image_file_background_color(image_file, self.format)
        return color

    def _update_from_image_field(self, instance, created, *args, **kwargs):
        if not instance or not instance.pk or not self.image_field:
            return
        # check if the field is a valid ImageField
        try:
            field_cls = instance._meta.get_field(self.image_field)
            if not isinstance(field_cls, ImageField):
                raise ImproperlyConfigured(
                    "Invalid 'image_field' field type, "
                    "expected an instance of 'models.ImageField'."
                )
        except FieldDoesNotExist as error:
            raise ImproperlyConfigured(
                "Invalid 'image_field' field name, "
                f"{self.image_field!r} field not found."
            ) from error
        # update value from picking color from image field
        color = self._get_image_field_color(instance)
        color_field_name = self.attname
        color_field_value = getattr(instance, color_field_name, None)
        if color_field_value != color and color:
            color_field_value = color or self.default
            # update in-memory value
            setattr(instance, color_field_name, color_field_value)
            # update stored value
            manager = instance.__class__.objects
            manager.filter(pk=instance.pk).update(
                **{color_field_name: color_field_value}
            )

class SiteConfig(models.Model):
    name = models.CharField(max_length=255)
    """The name of the site, to be displayed in the header and other places."""

    icon = models.CharField(max_length=255, null=True, blank=True)
    """The URL to the icon to use for this site. If not set, the default will be used."""

    style_sheet = models.CharField(max_length=255, null=True, blank=True)
    """The URL to the stylesheet to use for this site. If not set, the default will be used."""

    use_demo_mode = models.BooleanField(default=False)
    """Whether to use the demo mode for this site. This will not show competitions to anyone besides the creator. """

    def __str__(self) -> str:
        return f"SiteConfig(name={self.name})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to="profile_pics", default="static/default_pfp.jpg")

    def __str__(self) -> str:
        return f"Profile for {self.user}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# @receiver(post_save, sender=Competition)
# def save_user_profile(sender, instance, **kwargs):
#     if Competition.objects.filter(user=instance).exists():
#         instance.profile.save()
#     else:
#         Profile.objects.create(user=instance)

class Status(models.TextChoices):
    SETUP = "SETUP", _("Setup")  # for entries
    OPEN = "OPEN", _("Open")  # for judging
    CLOSED = "CLOSED", _("Closed")  # for judging
    COMPLETE = "COMPLETE", _("Complete")  # ready to show results
    ARCHIVED = "ARCHIVED", _("Archived")  # don't show to anyone (but data will be kept)
    
    __all__ = [SETUP, OPEN, CLOSED, COMPLETE, ARCHIVED]

    @classmethod
    def max_length(cls):
        lengths = [len(member.value) for member in cls]
        return max(lengths)
    
    @property
    def is_viewable(self) -> bool:
        """Whether the object should show up on the website."""
        return self in [__class__.OPEN, __class__.COMPLETE, __class__.CLOSED]

    @property
    def is_judgable(self) -> bool:
        """Whether judging for this comptetation should be allowed."""
        return self == __class__.OPEN
    
    @property
    def is_archived(self) -> bool:
        return self == __class__.ARCHIVED
    
    @property
    def is_in_setup(self) -> bool:
        return self == __class__.SETUP

class StatusField(models.CharField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs['max_length'] = Status.max_length()
        kwargs['choices'] = Status.choices
        kwargs['default'] = Status.SETUP
        super().__init__(*args, **kwargs)

class Sport(models.Model):
    name = models.CharField(max_length=255, unique=True)

    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sports', default=User.objects.get(username='admin').pk)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sports')
    """The user that created this object. This is used only if DEMO mode is on."""

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'owner']

class Organization(models.Model): # probably mostly schools but could also be community organizations
    name = models.CharField(max_length=257) # not unique because there could be schools with the same name just in different cities
    # logo = models.ImageField()
    # Attempt at an international-ambiguous addressing 
    # address_line1 = models.CharField(max_length=255) # Calle América 3
    # address_line2 = models.CharField(max_length=255) # Pozuelo de Alarcón 28224
    # address_line3 = models.CharField(max_length=255) # Madrid, Spain
    # related: teams
    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizations', default=User.objects.get(username='admin').pk)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizations')
    """The user that created this object. This is used only if DEMO mode is on."""

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'owner']

    def __str__(self) -> str:
        return str(self.name)  # + " (" + self.address_line3 + ")"
    

class Team(models.Model):
    name = models.CharField(max_length=255)
    sport = models.ForeignKey(Sport, blank=True, null=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.CASCADE)
    coach = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)  # with special permissions to change info WRT the team
    # logo = models.ImageField()
    # related: competition_set, tournament_set, round1_matches, won_matches

    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams', default=User.objects.get(username='admin').pk)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams')
    """The user that created this object. This is used only if DEMO mode is on."""

    def __str__(self) -> str:
        return self.name + (_(" from ") + str(self.organization) if self.organization else "") # type: ignore
    
    class Meta:
        ordering = ['sport', 'organization', 'name']
        unique_together = ['organization', 'name', 'owner']


class Arena(models.Model):
    name = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    is_available = models.BooleanField(default=True)
    color = ColorField(default="#CBCBCB")
    
    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='arenas', default=User.objects.get(username='admin').pk)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='arenas')
    """The user that created this object. This is used only if DEMO mode is on."""

    @property
    def is_dark(self) -> bool:
        color = str(self.color).lstrip('#')
        rgb = list(int(color[i:i+2], 16) for i in (0, 2, 4))
        hsp = math.sqrt(0.299 * (rgb[0] * rgb[0]) + 0.587 * (rgb[1] * rgb[1]) + 0.114 * (rgb[2] * rgb[2]))
        return hsp < 127.5

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'owner']

class Competition(models.Model):
    name = models.CharField(max_length=255, blank=True)
    sport = models.ForeignKey(Sport, blank=True, null=True, on_delete=models.SET_NULL)
    status = StatusField()
    start_date = models.DateField()
    end_date = models.DateField()
    #? how much flexibility needed as far as shifting events to different days
    # address_line1 = models.CharField(max_length=255)
    # address_line2 = models.CharField(max_length=255)
    # address_line3 = models.CharField(max_length=255)
    teams = models.ManyToManyField(Team, blank=True) # registered
    plenary_judges = models.ManyToManyField(User, blank=True)  # people entrusted to judge this competition as a whole: won't restrict them to a specific event
    access_key = models.CharField(max_length=ACCESS_KEY_LENGTH, default=get_random_access_key, blank=True, null=True)
    # For scheduling purposes, we need to be able to specify for this competition how many different (Event-specific) arenas are available and their capacity
    arenas = models.ManyToManyField(Arena, blank=False)
    host = models.ForeignKey(Organization, blank=True, null=True, on_delete=models.SET_NULL)

    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competitions', default=User.objects.get(username='admin').pk)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='competitions')
    """The user that created this object. This is used only if DEMO mode is on."""
    
    #all sorting are for sorting team scorings on competition results page
    
    def get_results(self):
        totals = dict() #this will be each team’s total points
        tournaments = SingleEliminationTournament.objects.filter(competition__id=self.id, status=Status.COMPLETE).order_by("-name", "points")
        robin = RoundRobinTournament.objects.filter(competition__id=self.id, status=Status.COMPLETE).order_by("-name")
        if tournaments:
            for tournament in tournaments:
                winners = tournament.winner
                if len(winners) > 1:#multiple winners
                    for winner in winners:
                        if winner.name in totals.keys():
                            totals[winner.name] = totals.get(winner) + float(tournament.points)
                        else:
                            totals[winner.name] = float(tournament.points)
                if len(winners) == 1:
                    winner = winners[0]
                    if winner in totals.keys():
                        totals[winner] = totals.get(winner) + float(tournament.points)
                    else:
                        totals[winner] = float(tournament.points)
        if robin:
            for tournament in robin:
                if tournament.status == Status.COMPLETE:
                    ppl = float(tournament.points_per_loss)
                    ppw = float(tournament.points_per_win)
                    ppt = float(tournament.points_per_tie)
                    for match in tournament.match_set.all():
                        num_winners = match.advancers.count()
                        for team in match.advancers.all():
                            if num_winners == 1:
                                if team.name in totals.keys():
                                    totals[team.name] = totals.get(team.name) + ppw
                                else:
                                    totals[team.name] = ppw
                            if num_winners > 1:
                                if team.name in totals.keys():
                                    totals[team.name] = totals.get(team.name) + ppt
                                else:
                                    totals[team.name] = ppt
                        starters = match.starting_teams.all()
                        winners = match.advancers.all()
                        for team in starters:
                            if team not in winners:
                                if team.name in totals.keys():
                                    totals[team.name] = totals.get(team.name) + ppl
                                else:
                                    totals[team.name] = ppl
        sorted_totals = {k:v for k,v in sorted(totals.items(), key=lambda item:item[1])}
        return sorted_totals

    def sort_by_team_names(self):
        dictionary = self.get_results
        sort_names = {k:v for k,v in sorted(dictionary.items(), key=lambda item:item[0])}
        return sort_names

    def sort_most_points(self):
        return self.get_results()

    def sort_least_points(self):
        most_to_least = self.get_results()
        least_to_most = {k:v for k,v in sorted(most_to_least.items(), key=lambda item:item[1], reverse=False)}
        return least_to_most 
    
    def sort_by_events_won(self):
        name_events_points = dict()
        sorted_events= dict()
        #extension: incorporate this into the get results, such as all tournaments with results
        if self.get_results:
            for team in self.teams:
                won_tournaments = list()
                overall_score = 0
                for tournament in AbstractTournament.objects.filter(teams=team, status=Status.COMPLETE):
                    last_match = Match.objects.filter(tournament=tournament).last()
                    if last_match.status == Status.COMPLETE and team in last_match.advancers:
                        won_tournaments.append(tournament.event.name)
                    if tournament.is_single_elimination:
                        overall_score = overall_score + tournament.points
                    else:
                        if last_match.advancers.count() == 1:
                            overall_score = overall_score + tournament.points_per_win
                        else:
                            overall_score = overall_score + tournament.points_per_tie
                won_tournaments = sorted(won_tournaments)
                name_events_points[team] = (won_tournaments, overall_score)
        sort_events_0 = {k: v for k, v in sorted(name_events_points.items(), key=lambda item: item[1][0])}
        sort_events = {k: v for k, v in sorted(sort_events_0.items(), key=lambda item: item[1][1])}
        return sort_events

    def get_winner(self):
        if self.status == Status.COMPLETE:
            totals = self.get_results()
            winners = list()
            if totals:
                greatest_score = max(totals.values())
                for key in totals:
                    if totals[key] == greatest_score:
                        team = Team.objects.filter(name=key).get()
                        winners.append(team)
                sorted_winners = sorted(winners, key=lambda t: t.name)
                return sorted_winners
            else:
                return ()
        else:
            return ()

    #check this auto completion method, should be if match is judged
    # def AUTO_COMPLETE_STATUS(self):
    #     tournaments = AbstractTournament.objects.filter(competition=self)
    #     if tournaments:
    #         for tournament in tournaments:
    #             matches = Match.objects.filter(tournament=tournament)
    #             last_match_status = matches.last().status
    #             if last_match_status == Status.COMPLETE:
    #                 tournament.status = Status.COMPLETE
    #                 tournament.save()
    #     if tournaments.filter(status=Status.COMPLETE) == tournaments:
    #         self.status = Status.COMPLETE
    #         self.save()

    def check_date(self):
        today = timezone.now().date()
        return self.end_date < today

    #checks if the competition has ended (true)
    #checks if the competition hasn't ended (false)

    @property
    def events(self):
        """Returns the events associated with this competition."""
        if DEMO:
            return Event.objects.filter(sport=self.sport, owner=self.owner)
        return Event.objects.filter(sport=self.sport)

    def __str__(self) -> str:
        # dwheadon: check if the name is unique for this year, otherwise add the month/day as well
        s: str = self.name # type: ignore
        qs = Competition.objects.filter(name=self.name)
        if DEMO: qs = qs.filter(owner=self.owner)

        if qs.count() > 1: # saves the queryset to a variable to avoid running the same query twice
            if (qs2 := (qs.filter(start_date__year=self.start_date.year))).count() > 1:
                if qs2.filter(start_date__month=self.start_date.month).exists():
                    # if you have two on the same day, good luck
                    s += f" {self.start_date.month}/{self.start_date.day}/{self.start_date.year}" # RoboMed June, 2023
                else:
                    s += f" {self.start_date.month}"
            else:
                s += f" {self.start_date.year}" # RoboMed June, 2023
        else:
            s += f" {self.start_date.year}" # RoboMed 2023
        return str(s)

    @property
    def max_capacity(self) -> int:
        return sum([arena.capacity for arena in self.arenas.all()])

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
        unique_together = ['start_date', 'name', 'owner'] # probably won't have 2 in the same year but you could have a quarterly / monthly / even weekly competition


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
    match_time = models.DurationField()
    sport = models.ForeignKey(Sport, blank=True, null=True, on_delete=models.SET_NULL)
    color = ColorField(default="#CBCBCB")
    # score_units = ScoreUnitsField() # initially just assume scores are place values (1st, 2nd, 3rd, etc.)
    # high_score_advances = models.BooleanField(default=True) # with seconds, low scores will usually advance (unless it's a "how long can you last" situation)
    # related: tournament_set
    use_units = models.BooleanField(default=False)
    units = models.CharField(max_length=25, default="point")
    units_verbose = models.CharField(max_length=26, default="points")
    use_higher_score = models.BooleanField(default=True)
    """whether the winner should win if their score is higher or lower. True=higher score wins, False=lower score wins."""

    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events', default=User.objects.get(username='admin').pk)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    """The user that created this object. This is used only if DEMO mode is on."""

    class Meta:
        ordering = ['sport', 'name', 'owner']

    def __str__(self) -> str:
        return str(self.name)

# dwheadon: can we force this to be abstract (non-instantiable)?
class AbstractTournament(models.Model):
    teams_per_match = models.PositiveSmallIntegerField(default=2)
    name = models.CharField(max_length=255, blank=True)
    #for times to work, we need to be add time-specific stuff in this model
    #tournament_starting_time, match_duration, and how many matches can occur per time period to name a few.
    status = StatusField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tournament_set") # besides helpfing to identify this tournament this will change how teams advance (high or low score)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="tournament_set")
    # interpolate_points = models.BooleanField(default=False) # otherwise winner takes all: RoboMed doesn't need this but it could be generally useful
    teams = models.ManyToManyField(Team, related_name="tournament_set")
    judges = models.ManyToManyField(User, blank=True, related_name="tournament_set")  # people entrusted to judge this tournament alone (as opposed to plenary judges)
    start_time = models.DateTimeField(default=timezone.now)
    points = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True) # for winner # dwheadon: is 10 digits / decimals enough / too much?
    # These Event-related things might depend on the competition: speed race with 1 v 1 at this competition but speed race with 4 v 4 at another (both are the same event)
    # max_teams_per_match = models.SmallIntegerField(default=2)
    max_teams_to_advance = models.SmallIntegerField(default=1)
    # teams_to_advance_rounds_up = models.BooleanField() # in a 4max/2adv situation if a match only has enough for say 3 competitors, do we advance two (round up) or 1 (round down)
    # tied_teams_all_advance = models.BooleanField()
    # dwheadon: what about tie_breakers? should we have a field for that?
    # related: match_set, ranking_set

    @property
    def owner(self):
        return self.competition.owner

    def __str__(self) -> str:
        return self.event.name + " " + ("single-elimination" if hasattr(self, "singleeliminationtournament") else "round-robin") + _(" tournament @ ") + str(self.competition) # SumoBot tournament at RoboMed 2023

    def get_end_time(self):
        time_in_seconds = 0
        if self.match_set and self.is_complete:
            for match in self.match_set:
                time_in_seconds = time_in_seconds + match.time
        added_time = datetime.timedelta(seconds=time_in_seconds)
        end_time = self.start_time + added_time
        return end_time

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

    @property
    def tournament_type(self) ->  str:
        return self.__class__.__name__

    # def __check_tournament_type(self, tournament_type: str) -> bool:
    #     """Private helper method for AbstractTournemnt to check if it is a certain type of tournament."""
    #     if issubclass(self.__class__, __class__):
    #         return self.tournament_type.lower().strip() == tournament_type.lower().strip()
    #     raise TypeError("This property is only available on subclasses of AbstractTournament")

    @property
    def is_single_elimination(self) -> bool:
        return SingleEliminationTournament.objects.filter(abstracttournament_ptr_id=self.id).exists()
    
    @property
    def is_round_robin(self) -> bool:
        return RoundRobinTournament.objects.filter(abstracttournament_ptr_id=self.id).exists()


    #create a dictionary with blank values for a tournament
    def create_tournament_tally(self):
        #full_dict_of_all_teams
        team_score_dict = dict()
        teams = self.teams
        for team in teams:
            team_score_dict[team] = 0
        #standard array
        #should update with the changes to the score
        return team_score_dict
        #not finished yet but will finish once I update the other methods
    
    class Meta:
        ordering = ['competition', 'event']

class Ranking(models.Model):
    """ These will determine the auto-layout of the brackets """
    tournament = models.ForeignKey(AbstractTournament, on_delete=models.CASCADE, related_name="ranking_set")
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField()

    def __str__(self) -> str:
        return f"{self.rank}) {self.team.name} in {self.tournament})"


    #to arrange a ranking system, consider history of teams
    #at the beginning, each team should be assigned a random ranking
    #then once the teams have finished a full tournament, rankings are sorted
    #add to the tournament model
    #def arrange_team_rankings(self):
    #   sorted_teams = list()
    #   num_of_teams = self.teams.count()
    #   for team in self.teams:
    #       #calculate all of their history of wins
            #overall score = 0
            #tournaments = Tournament.objects.filter(teams=team, status=Status.COMPLETE)
            #for tournament in tournaments:
            #   #collect their scores
            #sorted_teams.append(team, overall_score)
    #   sorted_teams.sort(key=lambda x: x[1])
    #   now determine seedings, check if values are tied, break tie randomly
    #verify seedings are proper

    class Meta:
        ordering = ['tournament', 'rank']
        unique_together = [['tournament', 'team']] 
        # unique_together += ['tournament', 'rank'] # NCAA has 4 teams with a #1 seed

class RoundRobinTournament(AbstractTournament):
    matches_per_team = models.PositiveSmallIntegerField()
    points_per_win = models.DecimalField(max_digits=20, decimal_places=10, default=3.0)
    points_per_tie = models.DecimalField(max_digits=20, decimal_places=10, default=1.0)
    points_per_loss = models.DecimalField(max_digits=20, decimal_places=10, default=0.0)

    @property
    def is_single_elimination(self) -> bool:   
        return False
    @property
    def is_round_robin(self) -> bool:
        return True

    # todo: rename to resolved
    @property
    def winner(self) -> list:
        if self.status == Status.COMPLETE:
            totals = dict()
            ppl = float(self.points_per_loss)
            ppw = float(self.points_per_win)
            ppt = float(self.points_per_tie)
            for match in self.match_set.all():
                num_winners = match.advancers.count()
                for team in match.advancers.all():
                    if num_winners == 1:
                        totals[team] = totals.get(team, 0) + ppw
                    if num_winners > 1:
                        totals[team] = totals.get(team, 0) + ppt
                starters = match.starting_teams.all()
                winners = match.advancers.all()
                for team in starters:
                    if team not in winners:
                        totals[team] = totals.get(team, 0) + ppl
            highest_score = max(totals.values())
            highest_scorers = []
            for team in totals:
                if totals[team] == highest_score:
                    highest_scorers.append(team)
            return highest_scorers

        else:
            return ()

    def get_points_for_each_team(self):
        team_colon_points = dict()
        for match in Match.objects.filter(tournament=self):
            if match.Status == Status.COMPLETE:
                if match.advancers.count() == 1 and self.points_per_win > 0:
                    team = match.advancers.first()
                    if team not in team_colon_points:
                        team_colon_points[team] = self.points_per_win
                    else:
                        original_score = team_colon_points[team]
                        team_colon_points[team] =  original_score + self.points_per_win
                if match.advancers.count() > 1 and self.points_per_tie > 0:
                    teams = match.advancers.all()
                    if team in teams:
                        team_colon_points[team] = self.points_per_tie
                    else:
                        original_score = team_colon_points[team]
                        team_colon_points[team] =  original_score + self.points_per_tie
                if self.points_per_loss > 0:
                    advancers = match.advancers.all()
                    for team in match.starting_teams.all():
                        if team not in advancers:
                            if team in teams:
                                team_colon_points[team] = self.points_per_loss
                            else:
                                original_score = team_colon_points[team]
                                team_colon_points[team] =  original_score + self.self.points_per_loss
        for team in self.competition.teams.all():
            if team not in team_colon_points:
                team_colon_points[team] = 0
        sorted_team_colon_points = dict(sorted(team_colon_points.items(), key=lambda item: item[1]))
        return sorted_team_colon_points

    def points_for_a_team(self, team):
        all_points = self.get_points_for_each_team()
        points = all_points[team]
        return points

    def points_against_a_team(self, team):
        total_points = 0
        for match in Match.objects.filter(tournament=self, starting_teams=team):
            if team not in match.advancers:
                #if you lost, then that is a point scored against you
                total_points = total_points + self.points_per_loss
        return total_points

    def points_scored_in_the_whole_tournament(self):
        completed_matches = Match.objects.filter(tournament=self, status=Status.COMPLETE)
        grand_total = 0
        for match in completed_matches:
            winning_teams = match.advancers.all()
            losing_teams = list()
            for team in match.starting_teams.all():
                if team not in winning_teams:
                    losing_teams.append(team)
            for team in match.prev_matches.last().advancers.all():
                if team not in winning_teams:
                    losing_teams.append(team)
            match_total = 0
            if winning_teams > 1:
                if self.points_per_tie:
                    match_total = match_total + float(self.points_per_tie*(winning_teams.count()))
            if winning_teams == 1:
                if self.points_per_win:
                    match_total = match_total + float(self.points_per_win)
            if self.points_per_loss:
                match_total = float(losing_teams.count()*self.points_per_loss)
            grand_total = grand_total + match_total
        return grand_total

    def win_loss_point_difference(self, team):
        #get the points awarded
        #get points against them
        #sub both
        awarded = self.points_for_a_team(self, team)
        lost = self.points_against_a_team(self, team)
        return "The point difference between the points awarded and the points lost by " + team.name + float(awarded-lost)

    class Meta():
        verbose_name = "Preliminary Tournament (Round Robin)"
        verbose_name_plural = "Preliminary Tournaments (Round Robin)"
#     ''' Everyone plays everyone else (most points / wins, wins) 
#         Can be used to establish rankings for an Elimination
#         This is often used for league play (not necessarily a tournament)
#     '''
#     # accumulation: sum of all points (e.g. goals), sum of match points (e.g. 2 for win, 1 for tie, 0 for loss)
#     # interpolated: rull rankings (order of points)

class SingleEliminationTournament(AbstractTournament):
    ''' Elimination style with brackets (last man standing) 
        Requires seedings determined by prior RoundRobin or expert input
        Seeding (ranking) is important because you want the last match to be close, not a total blowout
        Winner take all situation (1st place is really the only position that's established)
    '''
    prev_tournament = models.ForeignKey(RoundRobinTournament, on_delete=models.DO_NOTHING, blank=True, null=True)
    # interpolated: winner (of the top-level match)

    @property
    def is_single_elimination(self) -> bool:   
        return True

    @property
    def is_round_robin(self) -> bool:
        return False

    @property
    def winner(self) -> list:
        if self.status == Status.COMPLETE:
            advancers_qs = self.match_set.last().advancers.all()
            if advancers_qs.count() != 0:
                advancers = [advancer.name for advancer in advancers_qs]
                return advancers
        else:
            return []

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

class Match(models.Model):
    ''' Could be a one-off preliminary match or part of a larger tournament'''
    tournament = models.ForeignKey(AbstractTournament, models.CASCADE, blank=True, null=True, related_name="match_set")
    # Note: admin doesn't enforce the starting teams to be registered for this tournament
    starting_teams = models.ManyToManyField(Team, related_name="round1_matches", blank=True) # Only used for round1 matches, all others use the previous matches. Usually just 2 but could be more (speed race)
    # Note: admin doesn't restrict to previous matches from this tournament
    prev_matches = models.ManyToManyField('self', symmetrical=False, blank=True, related_name="next_matches") # Except for round1 of a tournament (or one-off preliminary matches), advancers from the previous matches will be the competitors for this match
    # Note: admin doesn't restrict advancers to be competitors for this match
    advancers = models.ManyToManyField(Team, related_name="won_matches", blank=True) # usually 1 but could be more (e.g. time trials)
    time = models.DateTimeField(blank=True, null=True) # that it's scheduled for
    arena = models.ForeignKey(Arena, related_name="match_set", on_delete=models.DO_NOTHING, blank=True, null=True)
    _cached_str = models.TextField(blank=True, null=True) # for caching the string representation
    round_num = models.PositiveIntegerField(default=1) # don't name it round, it overrides a built-in method (bad)
    """The round of the tournament that this match is in. 1 for the first round, 2 for the second, etc."""
    str_recursive_level: ClassVar[int] = 0

    history = HistoricalRecords()
    """History object for tracking changes to this model."""

    def get_competing_teams(self):
        return [
            team 
            for team in self.starting_teams.all()
        ] + [
            team 
            for prev_match in self.prev_matches.all() 
            for team in (prev_match.advancers.all() if prev_match.advancers.exists() else [None])
        ]

    @property
    def teams(self) -> List[Team]:
        return [team for team in self.starting_teams.all()] + [match.advancers.all() for match in [previous_match for previous_match in self.prev_matches.all()]]

    def _generate_str_recursive(self, force: bool=False) -> str:
        """Recursive algorithm for generating the string representation of this match.
        This is called whenever casted, and the result is saved to a variable to avoid recalculating it.
        It can be forced to recalculate by setting the force parameter to True, or passing in other kwargs"""
        if force or not self._cached_str:
            self.__class__.str_recursive_level += 1
            competitors = []
            if self.starting_teams.exists():
                competitors.extend((f"[{team.name}]" if team in self.advancers.all() else team.name) for team in self.starting_teams.all())
            if self.prev_matches.exists():
                for prev_match in self.prev_matches.all():
                    if prev_match.advancers.exists():
                        competitors.extend((f"[{team.name}]" if team in self.advancers.all() else team.name) for team in prev_match.advancers.all())
                    else:
                        competitors.append(f"Winner of ({prev_match})")
            self.__class__.str_recursive_level -= 1
            res = str(_(" vs ")).join(competitors) # Battlebots vs Byters
            if self.__class__.str_recursive_level == 0:
                self._cached_str =  res + _(" in ") + str(self.tournament) # Battlebots vs Byters in SumoBot tournament @ RoboMed 2023
            else: 
                self._cached_str =  res # if part of another match we don't want to repeat the tournament
            self.__class__.objects.filter(pk=self.pk).update(_cached_str=self._cached_str) # hack to save without sending the save signal which would get into an infinite recursive loop
        return str(self._cached_str)
    
    def __str__(self) -> str:
        self._generate_str_recursive()
        return f"""ID {self.id}, {self._cached_str}""" # type: ignore

    class Meta:
        ordering = ['tournament']
        verbose_name_plural = _('Matches')

class PointsEarned(models.Model):
    points = models.IntegerField(null=True)
    team = models.ForeignKey(Team, related_name="points_earned_set", on_delete=models.CASCADE)
    #(Harry) don't have time to implement this right now but here's the plan
    #using this system, you can filter by match and by team with something like
    #team.points_earned_set.filter(match=match)
    #since we can't do this into the html, we have to do it in the view functions
    #in the team data of each match, we check if the match has points or has been played
    #if both are true, we put the aforementioned function in the dictionary in some way
    #if not, then we put none, and this way, we can access the points earned in the html
    #and show it in the match bubbles.
    match = models.ForeignKey(Match, related_name="points_earned_set", on_delete=models.CASCADE)

    @staticmethod
    def get_points_for(match: Match, team: Team) -> int:
        """Gets the points for a given team and match. Returns -1 if no points are found.

        Args:
            match (Match): The match to get the points for.
            team (Team): The team to get the points for.

        Returns:
            int: The points earned by the team in the match.
        """
        try:
            points = __class__.objects.get(match=match, team=team).points
            assert points is not None
            return points
        except:
            return -1

@receiver(post_save, sender=Match)
def update_str_match(sender, instance, **kwargs):#
    instance._generate_str_recursive(force=True) # because kwargs are different, cache will not be used and we force it to recalculate

# https://github.com/h3/django-colorfield/blob/master/colorfield/fields.py 

# try:
#     from south.modelsinspector import add_introspection_rules
#     add_introspection_rules([], ["^colorfield\.fields\.ColorField"])
# except ImportError:
#     pass
