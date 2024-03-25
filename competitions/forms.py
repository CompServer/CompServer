

from django import forms
from django.contrib import messages

from competitions.models import AbstractTournament, Competition, SingleEliminationTournament, Team, Match, RoundRobinTournament


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

        for team in self.instance.advancers.all():
            if team not in self.possible_advancers.all():
                return False
        return super().is_valid()

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
        if self.cleaned_data['team1'] == self.cleaned_data['team2']:
            return False
        if self.cleaned_data['team1'] not in self.tournament.teams.all() or self.cleaned_data['team2'] not in self.tournament.teams.all():
            return False
        return super().is_valid()
        

# class CreateCompetitionsForm(forms.):
class CreateSETournamentForm(forms.ModelForm):
    generate_matches = forms.CheckboxInput()
    class Meta:
        model = SingleEliminationTournament
        fields = ['event', 'status', 'competition', 'points', 'teams', 'judges']

class CreateTournamentForm(forms.ModelForm):
    generate_matches = forms.CheckboxInput()
    class Meta:
        model = RoundRobinTournament
        fields = ['event', 'status', 'competition', 'points', 'teams', 'judges', 'num_rounds']