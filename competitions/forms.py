from typing import Optional

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, HTML, Layout, Submit
from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import TextInput
from django.urls import reverse_lazy

from competitions.models import (
    AbstractTournament,
    Arena,
    Competition,
    Match,
    RoundRobinTournament,
    SingleEliminationTournament,
    Sport,
    Team,
)
from competitions.utils import *

class JudgeForm(forms.ModelForm):
    possible_advancers = None

    def __init__(self, *args, possible_advancers, **kwargs):
        super().__init__(*args, **kwargs)
        if possible_advancers:
            self.fields['advancers'].queryset = possible_advancers

        self.possible_advancers = possible_advancers
        self.fields['advancers'].label = "Winning Teams"

    def is_valid(self):
        assert isinstance(self.instance, Match)
        # if hasattr(self, "possible_advancers"): return False
        # ^ above doesn't work, gotta use this try except -_-
        self.full_clean()
        if len(self.instance.teams) <= (self.cleaned_data.get('advancers', Team.objects.none()).count()):
            self.add_error('advancers', 'You cannot advance all teams in a match.')
            return False
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

# class TournamentSwapForm(forms.Form):
#     round_num = forms.IntegerField(label="Round")
#     team1 = forms.ModelChoiceField(queryset=None, label="Team 1")
#     team2 = forms.ModelChoiceField(queryset=None, label="Team 2")

#     def __init__(self, *args, tournament: AbstractTournament, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.tournament = tournament
#         self.fields['team1'].queryset = tournament.teams.all()
#         self.fields['team2'].queryset = tournament.teams.all()

#     def is_valid(self):
#         self.full_clean()
#         if self.cleaned_data['team1'] == self.cleaned_data['team2']:
#             return False
#         if self.cleaned_data['team1'] not in self.tournament.teams.all() or self.cleaned_data['team2'] not in self.tournament.teams.all():
#             return False
#         return super().is_valid()

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
        return super().is_valid()


class CreateCompetitionsForm(forms.ModelForm):
    def __init__(self, *args, owner: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.helper = FormHelper()
        self.helper.form_id = 'create_competition_form'
        self.helper.attrs = {
            'hx-post': reverse_lazy('competitions:create_competition'),
            'hx-target': '#competitions',
            'hx-swap': 'outerHTML',
        }
        self.helper.layout = Layout(
            Field('sport'),
            Field('name'),
            Field('status'),
            Field('teams'),
            HTML("""
                <div class="input-group mb-3">
                    <span class="input-group-text">New Team</span>
                    <input id="id_new_team" name="new_team" type="text" maxlength=255 class="textinput form-control"></input>
                    <button id="id_new_team_button" type="button" class="btn btn-primary" hx-post="/api/v1/teams/new/" hx-target="#id_teams" hx-on:htmx:after-request="document.getElementById('id_new_team').value='';">Add <i class="bi bi-arrow-up-short"></i></button>
                </div>
            """),  # Very hard-coded but don't know if it can be avoided
            Field('plenary_judges'),
            Field('start_date'),
            Field('end_date'),
            Field('arenas'),
            Submit('submit', 'Create Competition')
        )
        self.fields['sport'].queryset = Sport.objects.all()
        self.fields['sport'].widget.attrs = {
            'hx-get': '/api/v1/teams/',
            'hx-trigger': 'change',
            'hx-target': '#id_teams',
        }
        # This causes all teams to be invalid
        # self.fields['teams'].queryset = Team.objects.none()

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
            self.add_error('start_date', 'Start date must be before end date')
            self.add_error('end_date', 'End date must be after start date')
            return False
        for team in self.cleaned_data['teams']:
            if team.sport != self.cleaned_data['sport']:
                self.add_error('teams', 'All teams must be for the same sport.')
                return False
        # if self.cleaned_data['plenary_judges'].count() < 1:
        #     self.add_error('plenary_judges', 'You must select at least one plenary judge')
        #     return False
        self.instance.owner = self.owner
        return super().is_valid()

    class Meta:
        model = Competition
        fields = ['sport', 'name', 'status', 'teams', 'plenary_judges', 'start_date', 'end_date', 'arenas']
        widgets = {
            'start_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
            'end_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
        }

class SETournamentForm(forms.ModelForm):
    def __init__(self, *args, competition: Optional[Competition]=None, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['competition_field'].queryset = Competition.objects.filter(id=competition.id)
        self.helper = FormHelper(self)
        self.helper.form_id = 'create_setournament_form'
        self.fields['competition'].disabled = True
        if not kwargs.get('instance',None):
            assert competition is not None
            self.fields['competition'].initial = competition
        else:
            self.fields['competition'].initial = kwargs['instance'].competition
            competition = kwargs['instance'].competition
        self.fields['event'].queryset = competition.events
        self.fields['teams'].queryset = competition.teams.all()
        self.fields['teams'].initial = competition.teams.all()
        self.fields['points'].help_text = "How many points should be awarded to the winner?"
        self.fields['prev_tournament'].queryset = RoundRobinTournament.objects.filter(competition=competition)
        self.fields['prev_tournament'].label = "Previous Tournament"
        self.helper.add_input(Submit('submit', 'Save Tournament'))

    class Meta:
        model = SingleEliminationTournament
        fields = ['competition', 'status', 'teams', 'judges', 'event', 'points', 'prev_tournament', 'start_time']

class RRTournamentForm(forms.ModelForm):
    #generate_matches = forms.BooleanField(label='Generate Matches')
    #competition_field = forms.ModelChoiceField(queryset=None,label='Competition')

    def __init__(self, *args, competition: Optional[Competition]=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)

        self.helper.form_id = 'create_rrtournament_form'
        #self.fields['competition_field'].queryset = Competition.objects.filter(id=competition.id)
        self.fields['competition'].disabled = True
        if not kwargs.get('instance',None):
            assert competition is not None
            self.fields['competition'].initial = competition
        else:
            self.fields['competition'].initial = kwargs['instance'].competition
        self.fields['event'].queryset = competition.events
        self.fields['teams'].queryset = competition.teams.all()
        self.fields['teams'].initial = competition.teams.all()
        self.fields['points_per_win'].initial = round(self.fields['points_per_win'].initial, 2)
        self.fields['points_per_tie'].initial = round(self.fields['points_per_tie'].initial, 2)
        self.fields['points_per_loss'].initial = round(self.fields['points_per_loss'].initial, 2)
        #self.fields['points'].help_text = "How many points should be awarded to the winner?"
        #self.events = competition.events
        #self.fields['events'].queryset = Event.objects.filter(competition=competition)
        self.helper.add_input(Submit('submit', 'Save Tournament'))

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['teams_per_match'] > self.cleaned_data['teams'].count():
            self.add_error('teams_per_match', 'Teams per match must be less than or equal to the number of teams')
            return False
        elif self.cleaned_data['teams_per_match'] < 2:
            self.add_error('teams_per_match', 'Teams per match must be greater than or equal to 2')
            return False
        #extreme edge case
        elif self.cleaned_data['teams_per_match'] == 2 and self.cleaned_data['teams'].count() % 2 == 1 and self.cleaned_data['matches_per_team'] % 2 == 1:
            return False
        # elif self.cleaned_data['teams'].count() % self.cleaned_data['teams_per_match'] != 0:
        #     self.add_error('teams', 'Teams must be able to be divided evenly into matches')
        #     return False
        return super().is_valid()

    class Meta:
        model = RoundRobinTournament
        fields = ['competition', 'status', 'teams', 'judges', 'event', 'matches_per_team', 'teams_per_match', 'points_per_win', 'points_per_tie', 'points_per_loss', 'start_time']

class TournamentTypeSelectForm(forms.Form):
    tournament_type  = forms.MultipleChoiceField(
        choices=[('rr', 'Round Robin'), ('se', 'Single Elimination')],label="Tournament Type")

    def __init__(self, *args, competition_id: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'create_tournament_form'
        # self.helper.attrs = {
        #     'hx-post': f'/api/v1/tournament_form/{competition_id}/',
        #     #'hx-target': '#competitions',
        #     'hx-trigger': 'change', 
        #     'hx-swap': 'outerHTML',
        # }
        # self.tournament_type.widget.attrs = {
        self.fields['tournament_type'].widget.attrs = {
            'hx-post': f'/api/v1/tournament_form/{competition_id}/',
            'hx-trigger': 'change', 
            'hx-swap': 'innerHTML',
            'hx-target': '#secondary-form',
            #'hx-target': '',
            #'onchange': 'this.form.submit()',
        }
        #self.helper.add_input(Submit('submit', 'Create Tournament'))

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

class ArenaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['color'].widget = TextInput(attrs={"type": "color"})

    # def is_valid(self):
    #     self.full_clean()
    #     if self.cleaned_data['color'] == '#fff5a8':
    #         return False
    #     return super().is_valid()

    class Meta:
        model = Arena
        fields = ['capacity', 'color']
        template_name = 'competitions/arena.html'
        # success_url = "/"
