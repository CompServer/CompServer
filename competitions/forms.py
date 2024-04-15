

from django import forms
from django.contrib import messages
from django.forms.widgets import TextInput
from competitions.models import AbstractTournament, Competition, SingleEliminationTournament, Sport, Team, Match, RoundRobinTournament, Arena, ColorField
from .widgets import ColorPickerWidget, ColorWidget
from .utils import *
class JudgeForm(forms.ModelForm):
    possible_advancers = None

    def __init__(self, *args, possible_advancers, **kwargs):
        super().__init__(*args, **kwargs)
        if possible_advancers:
            self.fields['advancers'].queryset = possible_advancers

        self.possible_advancers = possible_advancers

    def is_valid(self):
        assert isinstance(self.instance, Match)
        # if hasattr(self, "possible_advancers"): return False
        # ^ above doesn't work, gotta use this try except -_-
        return all([team in self.possible_advancers.all() for team in self.instance.advancers.all()]) and super().is_valid()

    class Meta:
        model = Match
        fields = ['advancers']
        template_name = 'competitions/match_judge.html'
        success_url = "/"

class CompetitionStatusForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = ['status']
        
class TournamentStatusForm(forms.ModelForm):
    class Meta:
        model = AbstractTournament
        fields = ['status']

class TournamentSwapForm(forms.Form):
    round_num = forms.IntegerField(label="Round")
    team1 = forms.ModelChoiceField(queryset=None, label="Team 1")
    team2 = forms.ModelChoiceField(queryset=None, label="Team 2")

    def __init__(self, *args, tournament: AbstractTournament, **kwargs):
        super().__init__(*args, **kwargs)
        self.tournament = tournament
        self.fields['team1'].queryset = tournament.teams.all()
        self.fields['team2'].queryset = tournament.teams.all()

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['team1'] == self.cleaned_data['team2']:
            return False
        if self.cleaned_data['team1'] not in self.tournament.teams.all() or self.cleaned_data['team2'] not in self.tournament.teams.all():
            return False
        return super().is_valid()

class MatchSwapForm(forms.Form):
    match1 = forms.ModelChoiceField(queryset=None, label="Match 1")
    match2 = forms.ModelChoiceField(queryset=None, label="Match 2")

    def __init__(self, *args, tournament: AbstractTournament, **kwargs):
        super().__init__(*args, **kwargs)
        self.tournament = tournament
        self.fields['match1'].queryset = tournament.match_set.all()
        self.fields['match2'].queryset = tournament.match_set.all()

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['match1'] == self.cleaned_data['match2']:
            return False
        if self.cleaned_data['match1'] not in self.tournament.match_set.all() or self.cleaned_data['match2'] not in self.tournament.match_set.all():
            return False
        return super().is_valid()

class TeamSwapForm(forms.Form):
    teams1 = forms.ModelMultipleChoiceField(queryset=None, label="Teams 1")
    teams2 = forms.ModelMultipleChoiceField(queryset=None, label="Teams 2")

    def __init__(self, *args, match1: Match, match2: Match, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teams1'].queryset = match1.starting_teams.all()
        self.fields['teams2'].queryset = match2.starting_teams.all()

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['teams1'] == self.cleaned_data['teams2']:
            return False
        if isPlayed(teams1, match2.starting_teams.all()) or isPlayed(teams2, match1.starting_teams.all()):
            return False
        return super().is_valid()

class CreateCompetitionsForm(forms.ModelForm):

    def __init__(self, *args, sport: Sport, **kwargs):
        super().__init__(*args, **kwargs)
        self._sport: Sport = sport
        self.fields['teams'].queryset = Team.objects.filter(sport=sport)
        sportfield: forms.ModelMultipleChoiceField = self.fields['sport']
        sportfield.queryset = Sport.objects.filter(pk=sport.pk)
        sportfield.initial = sport
        sportfield.disabled = True

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
            self.add_error('start_date', 'Start date must be before end date')
            self.add_error('end_date', 'End date must be after start date')
            return False
        if self.cleaned_data['sport'] != self._sport:
            self.add_error('sport', 'Sport must be the same as the one in the URL')
            return False
        # if self.cleaned_data['plenary_judges'].count() < 1:
        #     self.add_error('plenary_judges', 'You must select at least one plenary judge')
        #     return False
        return super().is_valid()

    class Meta:
        model = Competition
        fields = ['name', 'status', 'sport', 'teams', 'plenary_judges', 'start_date', 'end_date', 'arenas']
        widgets = {
            'start_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
            'end_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
        }

# class CreateCompetitionsForm(forms.):
class CreateSETournamentForm(forms.ModelForm):
    generate_matches = forms.BooleanField(label='Generate Matches')
    #competition_field = forms.ModelChoiceField(queryset=None,label='Competition')

    def __init__(self, *args, competition: Competition, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['competition_field'].queryset = Competition.objects.filter(id=competition.id)
        self.fields['competition'].disabled = True
        self.fields['competition'].initial = competition
        self.event_queryset = competition.events
        self.fields['event'].queryset = self.event_queryset
        self.fields['teams'].queryset = competition.teams.all()
        self.fields['points'].help_text = "How many points should be awarded to the winner?"

        #self.events = competition.events
        #self.fields['events'].queryset = Event.objects.filter(competition=competition)

    class Meta:
        model = SingleEliminationTournament
        fields = ['status', 'points', 'teams', 'judges', 'event', 'competition']

class CreateRRTournamentForm(forms.ModelForm):
    generate_matches = forms.BooleanField(label='Generate Matches')
    #competition_field = forms.ModelChoiceField(queryset=None,label='Competition')

    def __init__(self, *args, competition: Competition, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['competition_field'].queryset = Competition.objects.filter(id=competition.id)
        self.fields['competition'].disabled = True
        self.fields['competition'].initial = competition
        self.event_queryset = competition.events
        self.fields['event'].queryset = self.event_queryset
        self.fields['teams'].queryset = competition.teams.all()
        #self.events = competition.events
        #self.fields['events'].queryset = Event.objects.filter(competition=competition)

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['teams_per_match'] > self.cleaned_data['teams'].count():
            self.add_error('teams_per_match', 'Teams per match must be less than or equal to the number of teams')
            return False
        elif self.cleaned_data['teams_per_match'] < 2:
            self.add_error('teams_per_match', 'Teams per match must be greater than or equal to 2')
            return False
        # elif self.cleaned_data['teams'].count() % self.cleaned_data['teams_per_match'] != 0:
        #     self.add_error('teams', 'Teams must be able to be divided evenly into matches')
        #     return False
        return super().is_valid()

    class Meta:
        model = RoundRobinTournament
        fields = ['competition', 'status', 'teams', 'judges', 'event', 'matches_per_team', 'teams_per_match', 'points_per_win', 'points_per_tie', 'points_per_loss']

class ArenaColorForm(forms.Form):
    arena = forms.ModelChoiceField(queryset=None, label="Arena")
    color = forms.CharField(widget=None, label="Color")
    def __init__(self, *args, competition: Competition, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = competition
        self.fields['arena'].queryset = competition.arenas.all()
        self.fields['color'].widget = TextInput(attrs={"type": "color"})

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['color'] == '#fff5a8':
            return False
        return super().is_valid()