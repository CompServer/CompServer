from django.contrib import messages
from django.shortcuts import render
import math
from .models import *
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from .models import *

def BracketView(request, tournament_id):
    numTeams = len(AbstractTournament.objects.get(pk=tournament_id).teams.all())
    numRounds = math.ceil(math.log(numTeams, 2))
    bracket_array = [{} for _ in range(numRounds)]

    def read_tree(match, round, index):
        competitors = []
        prior_match_advancing_teams = Team.objects.filter(won_matches__in=match.prev_matches.all())
        if match.starting_teams.exists():
            competitors += [(("[" + team.name + "]") if team in match.advancers.all() else team.name) for team in match.starting_teams.all()]
        if prior_match_advancing_teams:
            competitors += [(("[" + team.name + "]") if team in match.advancers.all() else team.name) for team in prior_match_advancing_teams]

        bracket_array[round][index] = competitors 

        prevs = match.prev_matches.all()
        if not prevs:
            return
        for i, prev in enumerate(prevs):
            read_tree(prev, round-1, 2*index+i)

    #mutates bracket_array
    read_tree(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True)[0], numRounds-1, 0)

    round_data = []
    matchWidth = 200
    connectorWidth = 50
    bracketWidth = (matchWidth+connectorWidth)*numRounds
    bracketHeight = numTeams*100
    roundHeight = bracketHeight
    roundWidth = matchWidth+connectorWidth
    for i in range(numRounds):
        num_matches = 2 ** (numRounds - i - 1)
        match_height = roundHeight / num_matches
        match_width = matchWidth

        match_data = []
        for j in range(num_matches):

            num_teams = 1
            team_data = []
            if j in bracket_array[i] and bracket_array[i][j] is not None:
                num_teams = len(bracket_array[i][j])
                team_data = [
                    {"team_name": bracket_array[i][j][k]}
                    for k in range(num_teams)
                ]
            
            team_height = 25
            center_height = team_height * num_teams
            top_padding = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": match_width,
                "center_height": center_height,
                "top_padding": top_padding,
            })

        round_data.append({
            "match_data": match_data,
        })

    bracket_dict = {
        "bracketWidth": bracketWidth,
        "bracketHeight": bracketHeight,
        "roundWidth": roundWidth+connectorWidth,
        "roundHeight": bracketHeight,
        "round_data": round_data
    }
    
    context = {"bracket_dict": bracket_dict,}
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
        status = competetion.status
        assert isinstance(status, Status)

        if not status.is_judgable:
            return False

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
