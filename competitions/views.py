from datetime import datetime
import math

from django.contrib import messages
from django.shortcuts import render, get_object_or_404
import math, random
from .models import *
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
 
from .models import *
from .forms import *

def home(request):
    #context = {'test_time': datetime.now()}
    #print(context['test_time'])
    return render(request, "competitions/home.html", )#context=context)

def is_overflowed(list1, num):
    for item in list1:
        if item < num:
            return False
    return True

def sort_list(list1, list2):
    z = [x for _, x in sorted(zip(list2, list1))]
    return z

def generate_single_elimination_matches(request, tournament_id):
    #sort the list by ranking, then use a two-pointer alogrithm to make the starting matches
    tournament = get_object_or_404(AbstractTournament, pk=tournament_id)
    team_ranks = []
    for rank in tournament.ranking_set.all():
        team_ranks.append((rank.team, rank.rank))
    team_ranks.sort(key=lambda x: x[1])
    #sort_list(teams, ranks)
    rank_teams = {}
    for i in range(len(rank_teams)):
        rank_teams[i+1] = team_ranks[i][0]
    num_teams = len(rank_teams)
    num_matches = 1
    extra_matches = []
    while num_matches * 2 < num_teams:
        num_matches *= 2
    i = 1
    while i < num_matches - (num_teams - num_matches):
        extra_matches.append(i)
        i += 1
    j = num_teams
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.starting_teams.add(rank_teams[i], rank_teams[j])
        match.save()
        extra_matches.append(match)
        i += 1
        j -= 1

    #regular starting matches
    i = 0
    j = num_matches - 1
    matches = []
    while i < j:
        match = Match.objects.create(tournament=tournament)
        if(isinstance(extra_matches[i], int)):
            match.starting_teams.add(extra_matches[i])
        else:
             match.prev_matches.add(extra_matches[i])
        if(isinstance(extra_matches[j], int)):
            match.starting_teams.add(extra_matches[j])
        else:
            match.prev_matches.add(extra_matches[j])
        match.save()
        matches.append(match)
        i += 1
        j -= 1
    num_matches = len(matches)

    #2nd round
    i = 0
    j = num_matches - 1
    new_matches = []
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.prev_matches.add(matches[i], matches[j])
        match.save()
        new_matches.append(match)
        i += 2
        j -= 2
    i = 1
    j = num_matches - 2
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.prev_matches.add(matches[i], matches[j])
        match.save()
        new_matches.append(match)
        i += 2
        j -= 2
    for match in new_matches:
        matches.append(match)
    num_matches = len(matches)

    #rest of the matches
    while num_matches > 1:
        new_matches = []
        for i in range(0, num_matches, 2):
            match = Match.objects.create(tournament=tournament)
            match.prev_matches.add(matches[i], matches[i+1])
            if i + 2 == num_matches - 1:
                match.prev_matches.add(matches[i+2])
            match.save()
            new_matches.append(match)
        matches = []
        for match in new_matches:
            matches.append(match)
        num_matches = len(matches)

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

# why are we using camelcase
def BracketView(request):
    t = ""

    numTeams = 8
    numRounds = int(math.log(numTeams, 2))

    roundWidth = 150
    bracketWidth = (roundWidth+30)*numRounds

    bracketHeight = 600
    roundHeight = bracketHeight
    roundWidth =    +connectorWidth
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

            if i is numRounds-1 and len(bracket_array[numRounds-i-1]) < len(bracket_array[numRounds-i-2]): 
                top_padding = match_data[-1]

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

@login_required
def single_elimination_tournament(request, tournament_id):
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    if request.method == 'POST':
        form = SETournamentStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            tournament.status = status
            tournament.save()
            # return HttpResponseRedirect(reverse("competitions:"))
    context = {"tournament": tournament, "user": request.user}
    return render(request, "competitions/single_elim_tournament.html", context)

@login_required
def tournaments(request):
    context = {"user": request.user}
    return render(request, "competitions/tournaments.html", context)

@login_required
def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "user": request.user, "form": CompetitionStatusForm()}
    return render(request, "competitions/competitions.html", context)

@login_required
def competition(request, competition_id):
    redirect_to = request.GET.get('next', '')
    redirect_id = request.GET.get('id', None)
    if redirect_id:
        redirect_id = [redirect_id]
    competition = get_object_or_404(Competition, pk=competition_id)
    if request.method == 'POST':
        form = CompetitionStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            competition.status = status
            competition.save()
            return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
    if competition.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    context = {"competition": competition, "user": request.user, "form": SETournamentStatusForm()}
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
    """
    Base view for not implemented features. You can  use this view to show a message to the user that the feature is not yet implemented,
    or if you want to add a view for a URL to a page that doesn't exist yet.
    """
    messages.error(request, "This feature is not yet implemented.")
    #raise NotImplementedError()
    return render(request, 'skeleton.html')


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
        raise PermissionDenied("This match is not judgable.")
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

def set_timezone_view(request):
    """
    View to set the timezone for the user.
    """
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        messages.success(request, f"Timezone set successfully to {request.POST['timezone']}.")
        return HttpResponseRedirect('/')
    else:
        return render(request, 'timezones.html', {'timezones': pytz.common_timezones, 'TIME_ZONE': request.session.get('django_timezone',None)})