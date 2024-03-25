

from django import forms
from django.contrib import messages

from competitions.models import Competition, SingleEliminationTournament, Sport, Team, Match, RoundRobinTournament


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

class RRTournamentStatusForm(forms.ModelForm):
    class Meta:
        model = RoundRobinTournament
        fields = ['status']

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

    def is_valid(self):
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
    