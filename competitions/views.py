from django.contrib import messages
from django.shortcuts import render
import math
from .models import *
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from .models import AbstractTournament, Competition, Match


def BracketView(request):
    t = ""

    numTeams = 8
    numRounds = int(math.log(numTeams, 2))

    roundWidth = 150
    bracketWidth = (roundWidth+30)*numRounds

    bracketHeight = 600
    roundHeight = bracketHeight

    t += f'<div class="bracket" style="height: {bracketHeight}px; width: {bracketWidth}px;">'    

    for i in range(0,numRounds):

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

            for k in range(0,numTeams):
                t += f'<div class="team" style="width: {matchWidth}px;">Team</div>'
            
            t += f'</div></div>'

        t += '</div>'

    t += '</div>'

    context = {"content":t,}
    return render(request, "competitions/bracket.html", context)


def tournament(request, tournament_id):
    return render(request, "competitions/tournament.html")


def tournaments(request):
    return render(request, "competitions/tournaments.html")


def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "Status": Status}
    return render(request, "competitions/competitions.html", context)


def team(request, team_id):
    context = {
        'team': Team.objects.get(id=team_id), #get a team from the team id passed into the view
    }
    return render(request, "competitions/team.html", context)


def not_implemented(request, *args, **kwargs):
    messages.error(request, "This feature is not yet implemented.")
    return render(request, 'skeleton.html')


def competition(request, competition_id):
    context = {
        'competition': Competition.objects.get(id=competition_id)
    }
    return render(request, "competitions/competition.html", context)


class JudgeMatchUpdateView(UserPassesTestMixin, AccessMixin, UpdateView):
    def test_func(self):
        user = self.request.user
        instance = self.get_object()
        assert isinstance(instance, Match)
        tournament = instance.tournament
        assert isinstance(tournament, AbstractTournament)
        competetion = tournament.competition
        assert isinstance(competetion, Competition)

        # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
        if user in tournament.judges.all() \
        or user in competetion.plenary_judges.all():# \
        #or user.is_superuser:
            return True
       # elif user.is_authenticated:
       #     returran PermissionDenied("You are not authorized to judge this match.")
        else:
            return False

    def handle_no_permission(self):
        return HttpResponseRedirect('/')
    
    permission_denied_message = "You are not authorized to judge this match."

    model = Match
    fields = ['advancers']
    template_name = 'match_judge.html'
    success_url = "/"
