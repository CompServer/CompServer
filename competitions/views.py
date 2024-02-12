from django import forms
from django.contrib import messages
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404, render
import math

from django.urls import reverse

from competitions.forms import JudgeForm
from .models import *
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin, UserPassesTestMixin
from .models import AbstractTournament, Competition, Match


# why are we using camelcase
def BracketView(request):
    t = ""

    numTeams = 8
    numRounds = int(math.log(numTeams, 2))

    roundWidth = 150
    bracketWidth = (roundWidth+30)*numRounds

    bracketHeight = 600
    roundHeight = bracketHeight

    t += f'<div class="bracket" style="height: {bracketHeight}px; width: {bracketWidth}px;">'    

    for i in range(numRounds):
        t += f'<div class="round" style="height: {roundHeight}px; width: {roundWidth}px;">'

        numMatches = 2**(numRounds-i-1)
        matchHeight = roundHeight/numMatches
        matchWidth = roundWidth

        for j in range(1, numMatches+1):

            numTeams = 2 if i!=0 else 4
            teamHeight = 25
            centerHeight = teamHeight*numTeams
            topPadding = (matchHeight-centerHeight)/2

            t += f'<div class="match" style="height: {matchHeight}px; width: {matchWidth}px;">'
            
            t += f'<div class="center" style="height: {centerHeight}px; padding-top: {topPadding}px">'

            for _ in range(0,numTeams):
                t += f'<div class="team" style="width: {matchWidth}px;">Team</div>'
            
            t += f'</div></div>'

        t += '</div>'

    t += '</div>'

    context = {"content":t,}
    return render(request, "competitions/bracket.html", context)


def tournament(request, tournament_id: int):
    return render(request, "competitions/tournament.html")

def tournaments(request):
    return render(request, "competitions/tournaments.html")

def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "Status": Status}
    return render(request, "competitions/competitions.html", context)


def team(request, team_id: int):
    context = {
        'team': get_object_or_404(Team, id=team_id)
    }
    return render(request, "competitions/team.html", context)


def not_implemented(request, *args, **kwargs):
    """Base view for not implemented features. You can  use this view to show a message to the user that the feature is not yet implemented,
    or want to link to a URL to a page that doesn't exist yet.
    """
    messages.error(request, "This feature is not yet implemented.")
    #raise NotImplementedError()
    return render(request, 'skeleton.html')

def competition(request, competition_id):
    context = {
        'competition': get_object_or_404(Competition, id=competition_id),
    }
    return render(request, "competitions/competition.html", context)

@login_required
def judge_match(request, match_id: int):
    instance = get_object_or_404(Match, pk=match_id)
    user = request.user

    tournament = instance.tournament
    assert isinstance(tournament, AbstractTournament)
    competetion = tournament.competition
    assert isinstance(competetion, Competition)
    
    if not competetion.is_judgable or not tournament.is_judgable:
        messages.error(request, "This match is not judgable.")
        return HttpResponseRedirect(reverse('competitions:competition', args=[competetion.id]))
    # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
    if  not (user in tournament.judges.all() \
    or user in competetion.plenary_judges.all()):# \
    #or user.is_superuser:
        messages.error(request, "You are not authorized to judge this match.")
        raise PermissionDenied("You are not authorized to judge this match.")
        #return HttpResponseRedirect(reverse('competitions:competition', args=[competetion.id]))

    if request.method == 'POST':
        form = JudgeForm(request.POST, instance=instance, possible_advancers=None)
        if form.is_valid():
            form.save()
            messages.success(request, "Match judged successfully.")

    winner_choices = []
    if instance.prev_matches.exists():
        winner_choice_ids = []
        for match in instance.prev_matches.all():
            winner_choice_ids.extend([x.id for x in match.advancers.all()])
        winner_choices = Team.objects.filter(id__in=winner_choice_ids)
    elif instance.starting_teams.exists():
        winner_choices = instance.starting_teams.all()
    form = JudgeForm(instance=instance, possible_advancers=winner_choices)
    return render(request, 'competitions/match_judge.html', {'form': form})

# class JudgeMatchUpdateView(UserPassesTestMixin, LoginRequiredMixin, UpdateView):
#     def test_func(self):
#         user = self.request.user

#         instance = self.get_object()
#         assert isinstance(instance, Match)
#         tournament = instance.tournament
#         assert isinstance(tournament, AbstractTournament)
#         competetion = tournament.competition
#         assert isinstance(competetion, Competition)
#         status = competetion.status
#         assert isinstance(status, Status)

#         if not status.is_judgable:
#             return False

#         # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
#         if user in tournament.judges.all() \
#         or user in competetion.plenary_judges.all():# \
#         #or user.is_superuser:
#             return True
#        # elif user.is_authenticated:
#        #     returran PermissionDenied("You are not authorized to judge this match.")
#         else:
#             return False

#     winners = forms.ModelMultipleChoiceField(label='winners', queryset=Team.objects.all(), required=True)

#     def handle_no_permission(self):
#         messages.error(self.request, "You are not authorized to judge this match.")
#         return HttpResponseRedirect('/')

#     permission_denied_message = "You are not authorized to judge this match."
#     template_name = 'competitions/match_judge.html'
#     success_url = "/"
#     model = Match
#     login_url = '/login/' # change to login url
#     redirect_field_name = 'redirect_to'

#     def __init__(self, *args, **kwargs) -> None:
#         super().__init__(*args, **kwargs)
#         instance = self.get_object()
#         assert isinstance(instance, Match)
#         if instance:
#             assert isinstance(instance, Match)
#             winner_choices = []
#             if instance.starting_teams:
#                 winner_choices = [*instance.starting_teams.all()]
#             elif instance.prev_matches:
#                 for match in instance.prev_matches.all:
#                     winner_choices.append(*match.advancers.all())
                
#             self.fields['winners'].queryset = winner_choices
