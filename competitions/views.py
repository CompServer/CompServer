from datetime import datetime
from io import SEEK_CUR
import math

from django.contrib import messages
from django.core.exceptions import BadRequest
from django.shortcuts import render, get_object_or_404
import math, random
from .models import *
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
import random
import zoneinfo
from .forms import *

def is_overflowed(list1: list, num: int):
  return all(x >= num for x in list1)

def generate_single_elimination_matches(request: HttpRequest, tournament_id: int):
    #sort the list by ranking, then use a two-pointer alogrithm to make the starting matches
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    assert tournament is not None
    if not tournament.prev_tournament or not tournament.prev_tournament.ranking_set.exists():
        teams = tournament.teams.all()
        for i, team in enumerate(teams, start=1):
            rank = Ranking.objects.create(tournament=tournament,team=team,rank=i)
            rank.save()

    team_ranks = sorted([(rank.team, rank.rank) for rank in tournament.prev_tournament.ranking_set.all()], key=lambda x: x[1])
    #sort_list(teams, ranks)        
    rank_teams = {i+1: team_ranks[i][0] for i in range(len(team_ranks))}
    num_teams = len(rank_teams)
    num_matches, i = 1, 1
    extra_matches = []
    while num_matches * 2 < num_teams:
        num_matches *= 2
    while i <= num_matches - (num_teams - num_matches):
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
    j = len(extra_matches) - 1
    matches = []
    while i < j:
        match = Match.objects.create(tournament=tournament)
        if(isinstance(extra_matches[i], int)):
            match.starting_teams.add(rank_teams[extra_matches[i]])
        else:
            match.prev_matches.add(extra_matches[i])
        if(isinstance(extra_matches[j], int)):
            match.starting_teams.add(rank_teams[extra_matches[j]])
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
    matches = new_matches.copy()
    num_matches = len(matches)

    #rest of the matches
    while num_matches > 1:
        new_matches = []
        for i in range(0, num_matches, 2):
            match = Match.objects.create(tournament=tournament)
            match.prev_matches.add(matches[i], matches[i+1])
            match.save()
            new_matches.append(match)
        matches = []
        matches.extend(new_matches)
        num_matches = len(matches)
    return HttpResponseRedirect(reverse("competitions:single_elimination_tournament", args=(tournament_id,)))

def generate_round_robin_matches(request: HttpRequest, tournament_id):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    some_num_matches = tournament.num_matches
    some_num_teams = 4
    teams = [team for team in tournament.teams.all()]
    num_participated = [0 for _ in range(some_num_matches)]
    for i in range(len(teams)):
        for k in range(some_num_matches):
            if num_participated[i] < some_num_matches and not is_overflowed(num_participated, some_num_matches):
                match = Match.objects.create(tournament=tournament)
                match.starting_teams.add(teams[i])
                match_teams = set(teams[i])
                while(len(match_teams) < some_num_teams):
                    j = random.randint(0, len(teams)-1)
                    while(num_participated[j] >= some_num_matches):
                        j = random.randint(0, len(teams)-1)    
                    temp = len(match_teams)        
                    match_teams.add(teams[j])
                    if temp < len(match_teams):
                        num_participated[j] += 1
                match.save()
                num_participated[i] += 1
    return HttpResponseRedirect(reverse("competitions:round_robin_tournament", args=(tournament_id,)))
    #also, this could run infinitely, or at least for very long.
    #will do ordering of matches once the bracket is fully understood. 


def generate_round_robin_rankings(request: HttpRequest, tournament_id: int):
    #don't have time right now, but here's what you gotta do
    #put all teams in a list, sort list based on how many wins they had
    #create rankings from there, done
    pass


def home(request: HttpRequest):
    return render(request, "competitions/home.html")


def tournament(request: HttpRequest, tournament_id: int):
    if SingleEliminationTournament.objects.filter(abstracttournament_ptr_id=tournament_id).exists():
        return single_elimination_tournament(request, tournament_id)
    elif RoundRobinTournament.objects.filter(abstracttournament_ptr_id=tournament_id).exists():
        return round_robin_tournament(request, tournament_id)
    raise Http404

def single_elimination_tournament(request: HttpRequest, tournament_id: int):
    redirect_to = request.GET.get('next', '')
    redirect_id = request.GET.get('id', None)
    if redirect_id:
        redirect_id = [redirect_id]
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    if request.method == 'POST':
        form = SETournamentStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            tournament.status = status
            tournament.save()
            if redirect_id == None:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
    if tournament.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))

    # where all the matches get stored, only used in this function, not passed to template
    bracket_array = []
        
    def generate_competitor_data(team, prev, match):
        is_next = match.next_matches.exists()
        connector = None
        if is_next:
            queryset = match.next_matches.all()[0].prev_matches.all()
            midpoint = (queryset.count() - 1) / 2
            index = list(queryset).index(match)
            connector = "connector-down" if index < midpoint else "connector-up" if index > midpoint else "idk??"

        return {
            "name": team.name if team else "TBD",
            "won": team in match.advancers.all(),
            "is_next": is_next,
            "prev": prev,
            "match_id": match.id,
            "connector": connector,
        }
    
    def read_tree_from_node(curr_match, curr_round, base_index):
        if len(bracket_array) <= curr_round:
            bracket_array.append({})

        competitors = [
            generate_competitor_data(team, False, curr_match)
            for team in curr_match.starting_teams.all()
        ] + [
            generate_competitor_data(team, True, curr_match)
            for prev_match in curr_match.prev_matches.all()
            for team in (prev_match.advancers.all() if prev_match.advancers.exists() else [None])
        ]

        bracket_array[curr_round][base_index] = competitors 
        
        prevs = curr_match.prev_matches.all()
        if prevs:
            for i, prev in enumerate(prevs):

                read_tree_from_node(prev, curr_round+1, 2*base_index+i)
        else:
            if len(bracket_array) <= curr_round+1:
                bracket_array.append({})
            bracket_array[curr_round+1][base_index] = None

    read_tree_from_node(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True).first(), 0, 0)

    bracket_array.pop()

    #the number of rounds in the tournament: top 8, semi-finals, championship, etc
    numRounds = len(bracket_array)

    mostTeamsInRound = max(sum(len(teams) if teams else 0 for teams in round.values()) for round in bracket_array)

    round_data = []
    matchWidth, connectorWidth, teamHeight = 200, 25, 25
    bracketWidth = (matchWidth + (connectorWidth * 2)) * numRounds
    bracketHeight = mostTeamsInRound * 50
    roundWidth = matchWidth + connectorWidth

    for round_matches in reversed(bracket_array):
        num_matches = len(round_matches)
        match_height = bracketHeight / num_matches
        match_data = []

        for team_data in round_matches.values():
            num_teams = len(team_data) if team_data else 0
            center_height = teamHeight * num_teams
            center_top_margin = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "center_top_margin": center_top_margin,
            })

        round_data.append({"match_data": match_data})


    bracket_dict = {
        "bracketWidth": bracketWidth, 
        "bracketHeight": bracketHeight, 
        "roundWidth": roundWidth+connectorWidth, 
        "roundHeight": bracketHeight,
        "teamHeight": teamHeight,
        "connectorWidth": connectorWidth,
        "round_data": round_data,
    }
    
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    context = {"tournament": tournament, "bracket_dict": bracket_dict}
    return render(request, "competitions/bracket.html", context)


def round_robin_tournament(request: HttpRequest, tournament_id: int):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    context = {"tournament": tournament,}
    return render(request, "competitions/round_robin_tournament.html", context)

def tournaments(request: HttpRequest):
    return render(request, "competitions/tournaments.html")

def competitions(request: HttpRequest):
    competition_list = Competition.objects.all().order_by("-status", "start_date")
    context = {"competition_list": competition_list, "form": CompetitionStatusForm()}
    return render(request, "competitions/competitions.html", context)

def competition(request: HttpRequest, competition_id: int):
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
            if redirect_id == None:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
    if competition.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    context = {"competition": competition, "form": SETournamentStatusForm()}
    return render(request, "competitions/competition.html", context)

def credits(request: HttpRequest):
    return render(request, "competitions/credits.html")

def not_implemented(request: HttpRequest, *args, **kwargs):
    """
    Base view for not implemented features. You can  use this view to show a message to the user that the feature is not yet implemented,
    or if you want to add a view for a URL to a page that doesn't exist yet.
    """
    messages.error(request, "This feature is not yet implemented.")
    #raise NotImplementedError()
    return render(request, 'skeleton.html')


@login_required
def judge_match(request: HttpRequest, match_id: int):
    instance = get_object_or_404(Match, pk=match_id)
    user = request.user

    tournament = instance.tournament
    assert isinstance(tournament, AbstractTournament)
    competetion = tournament.competition
    assert isinstance(competetion, Competition)
    
    if not competetion.is_judgable or not tournament.is_judgable:
        messages.error(request, "This match is not judgable.")
        #print("This match is not judgable.")
        raise PermissionDenied("This match is not judgable.")
    # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
    if  not (user in tournament.judges.all() \
    or user in competetion.plenary_judges.all() \
    or user.is_superuser):# \
    #or user.is_superuser:
        messages.error(request, "You are not authorized to judge this match.")
        #print("You are not authorized to judge this match.")
        raise PermissionDenied("You are not authorized to judge this match.")
        #return HttpResponseRedirect(reverse('competitions:competition', args=[competetion.id]))

    winner_choices = []
    if instance.prev_matches.exists():
        winner_choice_ids = []
        for match in instance.prev_matches.all():
            if match.advancers.exists():
                winner_choice_ids.extend([x.id for x in match.advancers.all()])
            else:
                messages.error(request, "One or more previous matches have not been judged.")
                #print("One or more previous matches have not been judged.")
                raise BadRequest("One or more previous matches have not been judged.")
        winner_choices = Team.objects.filter(id__in=winner_choice_ids)
    elif instance.starting_teams.exists():
        winner_choices = instance.starting_teams.all()
    else:
        messages.error(request, "This match has no starting teams or previous matches.")
        #print("This match has no starting teams or previous matches.")
        raise PermissionDenied("This match has no starting teams or previous matches.")

    if request.method == 'POST':
        form = JudgeForm(request.POST, instance=instance, possible_advancers=winner_choices)
        if form.is_valid():
            form.save()
            messages.success(request, "Match judged successfully.")
            #print("Match judged successfully.")
            return HttpResponseRedirect(reverse('competitions:judge_match', args=[instance.id]))

    form = JudgeForm(instance=instance, possible_advancers=winner_choices)
    return render(request, 'competitions/match_judge.html', {'form': form})

def set_timezone_view(request: HttpRequest):
    if request.method == "POST":
        if request.POST["timezone"]:
            request.session["timezone"] = request.POST["timezone"]
            messages.success(request, f"Timezone set successfully to {request.POST['timezone']}.")
            return redirect("/")
        else:   
            messages.error(request, "Invalid timezone.")
    timezones = sorted(zoneinfo.available_timezones())
    return render(request, "timezones.html", {"timezones": timezones})

def team(request: HttpRequest, team_id: int):
    today = timezone.now().date()
    upcoming_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id), tournament__competition__start_date__lte=today, tournament__competition__end_date__gte=today, advancers=None).order_by("-time")
    past_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id)).exclude(advancers=None).order_by("-time")
    unchecked_won_matches = past_matches.filter(advancers__id = team_id)
    official_won_matches = []
    for match in unchecked_won_matches:
        if match.advancers.count() == 1:
            official_won_matches.append(match)
    #need to order the time
    #can someone figure out how to annotate the query set and count the advancers?
    unchecked_draw_matches = past_matches.filter(advancers__id = team_id)
    official_draw_matches = []
    for match in unchecked_draw_matches:
        if match.advancers.count() > 1:
            official_draw_matches.append(match)
    lost_matches = past_matches.exclude(advancers__id = team_id).order_by("-time")
    past_tournaments = SingleEliminationTournament.objects.filter(teams__id = team_id, status = Status.COMPLETE)
    #how do you use properties in query sets?
    won_tournaments = []
    if past_tournaments.exists():
        for tournament in past_tournaments:
            matches = Match.objects.filter(tournament__id = tournament.id)
            for match in matches:
                if team in match.advancers.all():
                    won_tournaments.append(tournament)
    past_competitions = Competition.objects.filter(teams__id = team_id, status = Status.COMPLETE).order_by("end_date")
    context = {
        'team': Team.objects.get(pk=team_id),
        'upcoming_matches': upcoming_matches,
        'won_matches': official_won_matches,
        'past_matches': past_matches,
        'draw_matches': official_draw_matches,
        'lost_matches': lost_matches,
        'won_tournaments': won_tournaments,
        #how do you order tournaments by time?
        'past_tournaments': past_tournaments,
        'past_competitions': past_competitions,
    }
    return render(request, "competitions/team.html", context)