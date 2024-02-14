from django.contrib import messages
from django.shortcuts import render, get_object_or_404
import math, random
from .models import *
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.models import User

def is_overflowed(list1, num):
    for item in list1:
        if item < num:
            return False
    return True

def generate_single_elimination_matches(request, tournament_id):
    #sort the list by ranking, then use a two-pointer alogrithm to make the starting matches
    #figure out how to do the next matches later.
    tournament = get_object_or_404(AbstractTournament, pk=tournament_id)
    teams = {}
    max = 0
    for rank in tournament.ranking_set.all:
        teams[rank.rank] = rank.team
        if rank.rank > max:
            max = rank.rank
    i = 0
    j = 0
    if max % 2 == 1:
        i = 1
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.starting_teams.add(teams[i], teams[j])
        match.save()
        i += 1
        j -= 1
    # teams = []
    # num_participated = []
    # for team in tournament.teams.all():
    #     teams.append(team)
    #     num_participated.append(0)
    # if len(teams) % 2 == 1:
    #     num_participated[0] = 1
    # for i in range(len(teams)):
    #     if num_participated[i] == 0 and not is_overflowed(num_participated, 1):
    #         j = random.randint(0, len(teams)-1)
    #         while(num_participated[j] == 1):
    #             j = random.randint(0, len(teams)-1)
    #         match = Match.objects.create(tournament=tournament)
    #         match.starting_teams.add(teams[i], teams[j])
    #         match.save()
    #         num_participated[i] += 1
    #         num_participated[j] += 1

def generate_round_robin_matches(request, tournament_id):
    some_num_matches = 4
    tournament = get_object_or_404(AbstractTournament, pk=tournament_id)
    teams = []
    num_participated = []
    for team in tournament.teams.all():
        teams.append(team)
        num_participated.append(0)
    for i in range(len(teams)):
        for k in range(some_num_matches):
            if num_participated[i] < some_num_matches and not is_overflowed(num_participated, some_num_matches):
                j = random.randint(0, len(teams)-1)
                while(num_participated[j] >= some_num_matches):
                    j = random.randint(0, len(teams)-1)
                match = Match.objects.create(tournament=tournament)
                match.starting_teams.add(teams[i], teams[j])
                match.save()
                num_participated[i] += 1
                num_participated[j] += 1
    #also, this could run infinitely, or at least for very long.
    #will do ordering of matches once the bracket is fully understood.
    return render(request, 'skeleton.html')

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

@login_required
def single_elim_tournament(request, tournament_id):
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    context = {"tournament": tournament, "user": request.user}
    return render(request, "competitions/single_elim_tournament.html", context)

@login_required
def tournaments(request):
    context = {"user": request.user}
    return render(request, "competitions/tournaments.html", context)

@login_required
def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "user": request.user}
    return render(request, "competitions/competitions.html", context)

@login_required
def competition(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    if competition.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    context = {"competition": competition, "user": request.user, "Status": Status}
    return render(request, "competitions/competition.html", context)

@login_required
def team(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    context = {'team': team, "user": request.user}
    return render(request, "competitions/team.html", context)

def credits(request):
    context = {"user": request.user}
    return render(request, "competitions/credits.html", context)

def not_implemented(request, *args, **kwargs):
    messages.error(request, "This feature is not yet implemented.")
    return render(request, 'skeleton.html')

class JudgeMatchUpdateView(UserPassesTestMixin, AccessMixin, UpdateView):
    def test_func(self):
        user = self.request.user
        instance = self.get_object()
        assert isinstance(instance, Match)
        tournament = instance.tournament
        assert isinstance(tournament, AbstractTournament)
        competition = tournament.competition
        assert isinstance(competition, Competition)
        status = competition.status
        assert isinstance(status, Status)

        if not competition.is_judgable and tournament.is_judgable:
            return False

        # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
        if user in tournament.judges.all() \
        or user in competition.plenary_judges.all():# \
        #or user.is_superuser:
            return True
       # elif user.is_authenticated:
       #     returran PermissionDenied("You are not authorized to judge this match.")
        return False

    def handle_no_permission(self):
        return HttpResponseRedirect('/')
    
    permission_denied_message = "You are not authorized to judge this match."

    model = Match
    fields = ['advancers']
    template_name = 'match_judge.html'
    success_url = "/"
