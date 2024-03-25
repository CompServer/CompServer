

from django import forms
from django.contrib import messages

from competitions.models import Competition, SingleEliminationTournament, Team, Match, RoundRobinTournament


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

class RRTournamentStatusForm(forms.ModelForm):
    class Meta:
        model = RoundRobinTournament
        fields = ['status']

class RRTournamentSwapForm(forms.ModelForm):
    class Meta:
        model = RoundRobinTournament
        fields = ['round', 'teams']

# class CreateCompetitionsForm(forms.):
class CreateSETournamentForm(forms.ModelForm):
    generate_matches = forms.CheckboxInput()
    class Meta:
        model = SingleEliminationTournament
        fields = ['event', 'status', 'competition', 'points', 'teams', 'judges']

class CreateRRTournamentForm(forms.ModelForm):
    generate_matches = forms.CheckboxInput()
    class Meta:
        model = RoundRobinTournament
        fields = ['event', 'status', 'competition', 'points', 'teams', 'judges', 'num_rounds']