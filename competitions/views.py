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
    test = Match.objects.filter(tournament=tournament_id).exclude(advancers=None)

    # This calculates the seeding order
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



    rankings = list(Ranking.objects.filter(tournament=tournament_id).order_by('rank'))
    numTeams = len(rankings)
    numRounds = math.ceil(math.log(numTeams, 2))



    # this creates the pairings of matches to be drawn
    def generate_bracket_array(numRounds):
        bracket_array = [None]*numRounds

        # Round 1
        poitions = generate_seed_array(numRounds)
        new = [None]* numTeams

        for i in range(0,numTeams):
            new[i] = rankings[poitions[i]-1]

        bracket_array[0] = new

        bracket_array[1] = [None]*8

        bracket_array[2] = [None]*4

        bracket_array[3] = [None]*2

        matches = Match.objects.filter(tournament=tournament_id)

        return bracket_array



    bracket_array = generate_bracket_array(numRounds)


    # the rest of this just draws the bracket data and works fine
    round_data = []
    matchWidth = 200
    connectorWidth = 50
    bracketWidth = (matchWidth+connectorWidth)*numRounds
    bracketHeight = numTeams*50
    roundHeight = bracketHeight
    roundWidth = matchWidth+connectorWidth
    for i in range(numRounds):
        num_matches = 2 ** (numRounds - i - 1)
        match_height = roundHeight / num_matches
        match_width = matchWidth

        match_data = []
        for j in range(0,num_matches*2,2):
            num_teams = 2
            team_height = 25
            center_height = team_height * num_teams
            top_padding = (match_height - center_height) / 2

            team_data = [
                {"team_name": str(bracket_array[i][j+k].rank) + ": " + str(bracket_array[i][j+k].team) if bracket_array[i][j+k] else "TBD"}
                for k in range(num_teams)
            ]

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
    
    context = {"bracket_dict": bracket_dict, "test":test}
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
