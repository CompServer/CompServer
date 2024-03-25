

from django import forms
from django.contrib import messages

from competitions.models import AbstractTournament, Competition, SingleEliminationTournament, Sport, Team, Match, RoundRobinTournament


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

class SETournamentStatusForm(forms.ModelForm):
    class Meta:
        model = SingleEliminationTournament
        fields = ['status']

class TournamentStatusForm(forms.ModelForm):
    class Meta:
        model = RoundRobinTournament
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

class CreateCompetitionsForm(forms.ModelForm):
    sport = forms.ModelChoiceField(queryset=None) # just for display
    teams = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, sport: Sport, **kwargs):
        super().__init__(*args, **kwargs)
        self._sport: Sport = sport
        self.fields['teams'].queryset = Team.objects.filter(sport=sport)
        sportfield: forms.ModelMultipleChoiceField = self.fields['sport']
        sportfield.queryset = Sport.objects.filter(pk=sport.pk)
        sportfield.initial = sport
        sportfield.disabled = True

    class Meta:
        model = Competition
        fields = ['name', 'status', 'plenary_judges', 'start_date', 'end_date', 'arenas']
        widgets = {
            'start_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
            'end_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
        }

# class CreateCompetitionsForm(forms.):
class CreateSETournamentForm(forms.ModelForm):
    events = forms.ModelMultipleChoiceField(queryset=None)
    generate_matches = forms.CheckboxInput()

    def __init__(self, competition: Competition, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = competition
        self.events_queryset = competition.events
        self.fields['events'].queryset = self.events_queryset
        #self.events = competition.events
        #self.fields['events'].queryset = Event.objects.filter(competition=competition)

    class Meta:
        model = SingleEliminationTournament
        fields = ['status', 'points', 'teams', 'judges']

class CreateRRTournamentForm(forms.ModelForm):
    
    events = forms.ModelMultipleChoiceField(queryset=None)
    generate_matches = forms.CheckboxInput()

    def __init__(self, competition: Competition, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition = competition
        self.events_queryset = competition.events
        self.fields['events'].queryset = self.events_queryset
        #self.events = competition.events
        #self.fields['events'].queryset = Event.objects.filter(competition=competition)

    class Meta:
        model = RoundRobinTournament
        fields = ['status', 'points', 'teams', 'judges', 'num_rounds']
    