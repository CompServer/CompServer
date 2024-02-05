from django.contrib import messages
from django.shortcuts import render
import math
from .models import *
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from .models import *

def generate_seed_array(round_num):
    #Triangular array read by rows in bracket pairs
    #https://oeis.org/A208569  
    def T(n, k):
        if n == 1 and k == 1:
            return 1
        
        elif k % 2 == 1:
            return T(n - 1, (k + 1) // 2)
            
        return 2**(n - 1) + 1 - T(n - 1, k // 2)

    return [T(round_num+1, k) for k in range(1, 2**(round_num) + 1)]


def BracketView(request, tournament_id):
    bracket = AbstractTournament.objects.get(pk=tournament_id)
    rankings = list(Ranking.objects.filter(tournament=tournament_id).order_by('rank'))
    bracket_dict = {}

    t = ""

    numTeams = len(rankings)/2
    numRounds = math.ceil(math.log(numTeams, 2))

    seed_array = generate_seed_array(numRounds)

    bracket_dict["roundWidth"] = 175
    bracket_dict["connectorWidth"] = 50
    bracketWidth = (roundWidth+connectorWidth)*numRounds
    bracketHeight = numTeams*50
    roundHeight = bracketHeight

    t += f'<div class="bracket" style="height: {bracketHeight}px; width: {bracketWidth}px;">'    

    for i in range(0,numRounds):
        t += f'<div class="round" style="height: {roundHeight}px; width: {roundWidth}px;">'

        numMatches = 2**(numRounds-i-1)
        matchHeight = roundHeight/numMatches
        matchWidth = roundWidth

        for j in range(0, numMatches):

            numTeams = 2
            teamHeight = 25
            centerHeight = teamHeight*numTeams
            topPadding = (matchHeight-centerHeight)/2

            t += f'<div class="match" style="height: {matchHeight}px; width: {matchWidth}px;">'
            t += f'<div class="center" style="height: {centerHeight}px; padding-top: {topPadding}px">'

            for k in range(0,numTeams):
                t += f'<div class="team" style="width: {matchWidth}px;">{rankings[seed_array[2*j + k]].team if i == 0 else "TBD"}</div>'
            
            t += f'</div></div>'
        t += '</div>'
    t += '</div>'

    context = {"content":t}
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
