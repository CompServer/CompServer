from typing import Optional
from django import forms
from django.contrib import messages
from django.db.models import QuerySet
from django.forms.widgets import TextInput
from django.urls import reverse_lazy
from competitions.models import AbstractTournament, Competition, SingleEliminationTournament, Sport, Team, Match, RoundRobinTournament, Arena, ColorField
from .widgets import ColorPickerWidget, ColorWidget
from .utils import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Team

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

# class CreateArenasForm(forms.ModelForm):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_id = 'create_arena_form'
#         self.helper.attrs = {
#             'hx-post': reverse_lazy('competitions:create_arena'),
#             'hx-target': '#arenas',
#             'hx-swap': 'outerHTML',
#         }
#         self.helper.add_input(Submit('submit', 'Create Arena'))
#         self.fields['name'].queryset = Arena.objects.all()
#         #self.fields['capacity'].queryset = 
#         #self.fields['is_available'].queryset =
#         #self.fields['color'].queryset = #color wheel
#         # self.fields[''].widget.attrs = {
#         #     'hx-get': '/api/v1/teams/',
#         #     'hx-trigger': 'change',
#         #     'hx-target': '#id_teams',
#         # }

#     def is_valid(self):
#         self.full_clean()
#         #check the color, boolean statement, integer
#         if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
#             self.add_error('start_date', 'Start date must be before end date')
#             self.add_error('end_date', 'End date must be after start date')
#             return False
#         for team in self.cleaned_data['teams']:
#             if team.sport != self.cleaned_data['sport']:
#                 self.add_error('teams', 'All teams must be for the same sport.')
#                 return False
#         # if self.cleaned_data['plenary_judges'].count() < 1:
#         #     self.add_error('plenary_judges', 'You must select at least one plenary judge')
#         #     return False
#         return super().is_valid()

#     class Meta:
#         model = Arena
#         fields = ['name', 'is_available', 'capacity', 'color']
#         widgets = {
#             #here is where you add widgets
#             #and a counter for the capacity
#             #select from a dropdown for true or false
#             'start_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
#             'end_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
#         }

# class CreateEventsForm(forms.ModelForm):
#     #name, match time, sport

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_id = 'create_event_form'
#         self.helper.attrs = {
#             'hx-post': reverse_lazy('competitions:create_event'),
#             'hx-target': '#events',
#             'hx-swap': 'outerHTML',
#         }
#         self.helper.add_input(Submit('submit', 'Create Event'))
#         self.fields['sport'].queryset = Sport.objects.all()
#         self.fields['sport'].widget.attrs = {
#             'hx-get': '/api/v1/teams/',#have to change these
#             'hx-trigger': 'change',
#             'hx-target': '#id_teams',
#         }
#         def is_valid(self):
#             self.full_clean()
#             if isinstance(self.cleaned_data['name'], str):
#                 self.add_error('name', 'Event name must be a string')
#                 return False
#             for sport in self.cleaned_data['sport']:
#                 if team.sport != self.cleaned_data['sport']:
#                     self.add_error('sport', 'You must select a valid sport.')
#                     return False
#             #add a number widget
#             #if self.cleaned_data['time']:
#             #get the date time for today
#             #check the date time of the competition to be later
#             return super().is_valid()

#         class Meta:
#             model = Event
#             fields = ['sport', 'name', 'match_time']
#             widgets = {#change these for match_time
#                 'start_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
#                 'end_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
#             }


# class CreateOrganizationsForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_id = 'create_organization_form'
#         self.helper.attrs = {
#             'hx-post': reverse_lazy('competitions:create_organization'),
#             'hx-target': '#organizations',
#             'hx-swap': 'outerHTML',
#         }
#         self.helper.add_input(Submit('submit', 'Create Organization'))

#         def is_valid(self):
#             self.full_clean()
#             if not isinstance(self.cleaned_data['name'], str):
#                 self.add_error('name', 'Organization name must be a string.')
#                 return False
#             return super().is_valid()

#         class Meta:
#             model = Organization
#             fields = ['name']

# class CreateSportsForm(forms.ModelFOrm):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_id = 'create_sport_form'
#         self.helper.attrs = {
#             'hx-post': reverse_lazy('competitions:create_sport'),
#             'hx-target': '#sports',
#             'hx-swap': 'outerHTML',
#         }
#         self.helper.add_input(Submit('submit', 'Create Sport'))
#         def is_valid(self):
#             self.full_clean()
#             if isinstance(self.cleaned_data['name'], str):
#                 self.add_error('name', 'Sport name must be a string')
#                 return False
#             return super().is_valid()

#         class Meta:
#             model = Sport
#             fields = ['name']

#class CreateTeamsForm(forms.ModelForm):

#need to finish tournament and arena creation forms

class CreateCompetitionsForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'create_competition_form'
        self.helper.attrs = {
            'hx-post': reverse_lazy('competitions:create_competition'),
            'hx-target': '#competitions',
            'hx-swap': 'outerHTML',
        }
        self.helper.add_input(Submit('submit', 'Create Competition'))
        self.fields['sport'].queryset = Sport.objects.all()
        self.fields['sport'].widget.attrs = {
            'hx-get': '/api/v1/teams/',
            'hx-trigger': 'change',
            'hx-target': '#id_teams',
        }

        self.fields['teams'].queryset = Team.objects.none()

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
        return super().is_valid()

    class Meta:
        model = Competition
        fields = ['sport', 'name', 'status', 'teams', 'plenary_judges', 'start_date', 'end_date', 'arenas']
        widgets = {
            'start_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
            'end_date': forms.DateInput(attrs={'format': 'yyyy-mm-dd','type':'date'}),
        }

#edit profile, delete bio, add photo/upload photo, delete photo

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
        #self.fields['color'].help_text = "Select a color from the color wheel" #list of colors
        #add color wheel to form
        if not self.instance:
            self.helper.add_input(Submit('submit', 'Create Tournament'))
        #self.events = competition.events
        #self.fields['events'].queryset = Event.objects.filter(competition=competition)

    class Meta:
        model = SingleEliminationTournament
        fields = ['competition', 'status', 'teams', 'judges', 'event', 'points', 'prev_tournament']


# class UploadProfilePhoto(forms.ModelForm):
#     def __init__(self, *args, profile: Optional[Profile]=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper(self)
#         self.helper.form_id = 'upload_profile_photo'
#         self.fields['profile'].disabled = True
#         if not kwargs.get('instance',None):
#             assert profile is not None
#             self.fields['profile'].initial = profile
#         else:
#             self.fields['profile'].initial = kwargs['instance'].profile
#             profile = kwargs['instance'].profile
#         self.fields['photo'].label = "Profile Photo"
#         if not self.instance:
#             self.helper.add_input(Submit('submit', 'Upload Photo'))
#     class Meta:
#         model = Profile
#         fields = ['user', 'profile_pic', 'bio']

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
        if not self.instance:
            self.helper.add_input(Submit('submit', 'Create Tournament'))

    def is_valid(self):
        self.full_clean()
        if self.cleaned_data['teams_per_match'] > self.cleaned_data['teams'].count():
            self.add_error('teams_per_match', 'Teams per match must be less than or equal to the number of teams')
            return False
        elif self.cleaned_data['teams_per_match'] < 2:
            self.add_error('teams_per_match', 'Teams per match must be greater than or equal to 2')
            return False
        elif self.cleaned_data['teams_per_match'] == 2 and self.cleaned_data['teams'].count() % 2 == 1 and self.cleaned_data['matches_per_team'] % 2 == 1:
            return False
        # elif self.cleaned_data['teams'].count() % self.cleaned_data['teams_per_match'] != 0:
        #     self.add_error('teams', 'Teams must be able to be divided evenly into matches')
        #     return False
        return super().is_valid()

    class Meta:
        model = RoundRobinTournament
        fields = ['competition', 'status', 'teams', 'judges', 'event', 'matches_per_team', 'teams_per_match', 'points_per_win', 'points_per_tie', 'points_per_loss']

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
