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
    '''
    This view is responsible for drawing the tournament bracket, it does this by:
    1) Recursively get all matches and put them in a 3d array
        a) Start at championship
        b) Get particpants and add them to the array
        c) Go to each prev match
        d) repeat
    2) Loop through array and convert it to dictionaries, packaging styling along side
    3) Pass new dictionary to the templete for rendering

    note: steps 1 and 2 could probably be combined
    '''
    # where all the matches get stored, only used in this function, not passed to template
    bracket_array = []

    # recursive
    def read_tree_from_node(curr_match, curr_round, base_index):
        # add space for new matches if it doesnt exist
        if len(bracket_array) <= curr_round:
            bracket_array.append({})

        # get the names of the teams competing, stolen to the toString
        competitors = []
        prior_match_advancing_teams = Team.objects.filter(won_matches__in=curr_match.prev_matches.all())
        if curr_match.starting_teams.exists():
            competitors += [(("[" + team.name + "]") if team in curr_match.advancers.all() else team.name) for team in curr_match.starting_teams.all()]
        if prior_match_advancing_teams:
            competitors += [(("[" + team.name + "]") if team in curr_match.advancers.all() else team.name) for team in prior_match_advancing_teams]

        # place the team names in the right box
        # i.e. bracket_array[2][3] = top 8, 4th match from the top
        bracket_array[curr_round][base_index] = competitors 

        
        prevs = curr_match.prev_matches.all()
        # checks if there are any previous matches
        if prevs:
            # if TRUE: recurse
            # if FALSE: base case
            for i, prev in enumerate(prevs):
                read_tree_from_node(prev, curr_round+1, 2*base_index+i)
                                                      # ^^^^^^^^^^^^^^
                                                      # i dont know why this works, it might not 

                

    #mutates bracket_array
    read_tree_from_node(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True)[0], 0, 0)

    #the number of rounds in the tournament: top 8, semi-finals, championship, etc
    numRounds = len(bracket_array)

    #find the most number of teams in a single round, used for setting the height
    mostTeamsInRound = 0
    for round in bracket_array:
        teams_count = sum(len(teams) for teams in round.values())
        if teams_count > mostTeamsInRound:
            mostTeamsInRound = teams_count

    # _data means it contains the actual stuff to be displayed
    # everything else is just css styling or not passed
    # most variables are exactly what they sound like
    # you can also look at bracket.html to see how its used
    round_data = []
    matchWidth = 200
    connectorWidth = 50
    bracketWidth = (matchWidth+connectorWidth)*numRounds
    bracketHeight = mostTeamsInRound*50
    roundHeight = bracketHeight
    roundWidth = matchWidth+connectorWidth
    for i in range(numRounds):
        num_matches = len(bracket_array[numRounds-i-1])
        match_height = roundHeight / num_matches
        match_width = matchWidth
        match_data = []
        for j in range(num_matches):
            team_data = []
            #this is where we convert from bracket_array (made above) to bracket_dict (used in template)
            if j in bracket_array[numRounds-i-1] and  bracket_array[numRounds-i-1][j] is not None:
                num_teams = len(bracket_array[numRounds-i-1][j])
                team_data = [
                    {"team_name": bracket_array[numRounds-i-1][j][k]}
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
