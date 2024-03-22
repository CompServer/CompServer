from datetime import datetime
from http.client import HTTPResponse
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.shortcuts import render, get_object_or_404
from django.utils.autoreload import start_django
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from io import SEEK_CUR
import random
import zoneinfo
from typing import Union
from .forms import *
from .models import *


def is_overflowed(list1: list, num: int):
  return all(x >= num for x in list1)


def get_tournament(request, tournament_id: int) -> Union[SingleEliminationTournament, RoundRobinTournament]:
    """Get a tournament by it's id, regardless of it's type.

    Args:
        tournament_id (int): The ID of the tournament.

    Raises:
        Http404: If the tournament does not exist or is not found.

    Returns:
        Union[SingleEliminationTournament, RoundRobinTournament]: The found tournament.
    """    
    if SingleEliminationTournament.objects.filter(abstracttournament_ptr_id=tournament_id).exists():
        return get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    elif RoundRobinTournament.objects.filter(abstracttournament_ptr_id=tournament_id).exists():
        return get_object_or_404(RoundRobinTournament, pk=tournament_id)
    raise Http404


def generate_tournament_matches(request: HttpRequest, tournament_id: int):
    """View that calls the corresponding generate method for the tournament type."""
    tournament = get_tournament(request, tournament_id)
    if isinstance(tournament, SingleEliminationTournament):
        return generate_single_elimination_matches(request, tournament_id)
    elif isinstance(tournament, RoundRobinTournament):
        return generate_round_robin_matches(request, tournament_id)
    raise Http404


def generate_single_elimination_matches(request, tournament_id):
    #sort the list by ranking, then use a two-pointer alogrithm to make the starting matches
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    arena_iterator = 0
    nmpt_iterator = 0
    arenas = [i for i in tournament.competition.arenas.filter(is_available=True)]
    starting_time = tournament.start_time 
    team_ranks = []
    if tournament.prev_tournament == None or not tournament.prev_tournament.ranking_set.exists():
        teams = tournament.teams.all()
        for i, team in enumerate(teams, start=1):
            rank = Ranking.objects.create(tournament=tournament,team=team,rank=i)
            rank.save()
            team_ranks.append((rank.team, rank.rank))
    else:
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
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time() 
        match.save()
        extra_matches.append(match)
        i += 1
        j -= 1

    #regular starting matches
    nmpt_iterator = 0
    if arena_iterator > 0:
        arena_iterator = 0
        starting_time += datetime.timedelta(minutes=10)
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
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time 
        match.save()
        matches.append(match)
        i += 1
        j -= 1
    num_matches = len(matches)

    #2nd round
    nmpt_iterator = 0
    if arena_iterator > 0:
        arena_iterator = 0
        starting_time += tournament.event.match_time
    i = 0
    j = num_matches - 1
    new_matches = []
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.prev_matches.add(matches[i], matches[j])
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time 
        match.save()
        new_matches.append(match)
        i += 2
        j -= 2
    i = 1
    j = num_matches - 2
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.prev_matches.add(matches[i], matches[j])
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time
        match.save()
        new_matches.append(match)
        i += 2
        j -= 2
    matches = new_matches.copy()
    num_matches = len(matches)

    #rest of the matches
    while num_matches > 1:
        nmpt_iterator = 0
        if arena_iterator > 0:
            arena_iterator = 0
            starting_time += tournament.event.match_time
        new_matches = []
        for i in range(0, num_matches, 2):
            match = Match.objects.create(tournament=tournament)
            match.prev_matches.add(matches[i], matches[i+1])
            match.time = starting_time
            match.arena = arenas[arena_iterator]
            nmpt_iterator += 1
            if nmpt_iterator == arenas[arena_iterator].capacity:
                arena_iterator += 1
                nmpt_iterator = 0
                if arena_iterator >= len(arenas):
                    arena_iterator = 0
                    starting_time += tournament.event.match_time 
            match.save()
            new_matches.append(match)
        matches = []
        matches.extend(new_matches)
        num_matches = len(matches)
    return HttpResponseRedirect(reverse("competitions:single_elimination_tournament", args=(tournament_id,)))

def generate_round_robin_matches(request, tournament_id):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    arena_iterator = 0
    nmpt_iterator = 0
    arenas = [i for i in tournament.competition.arenas.filter(is_available=True)]
    starting_time = tournament.start_time 
    teams = [team for team in tournament.teams.all()]
    prev_matches = []
    curr_prev = []
    for k in range(tournament.num_rounds):
        nmpt_iterator = 0
        if arena_iterator > 0:
            arena_iterator = 0
            starting_time += tournament.event.match_time
        num_participated = [0 for _ in range(len(teams))]
        while num_participated != [1 for _ in range(len(teams))]:
            match = Match.objects.create(tournament=tournament)
            for i in range(tournament.teams_per_match):
                j = random.randint(0, len(teams)-1)
                while(num_participated[j] > 0 or teams[j] in match.starting_teams.all()):
                    j = random.randint(0, len(teams)-1)          
                match.starting_teams.add(teams[j])
                num_participated[j] += 1 
                if num_participated == [1 for _ in range(len(teams))]:
                    break
            match.time = starting_time
            match.arena = arenas[arena_iterator]
            nmpt_iterator += 1
            if nmpt_iterator == arenas[arena_iterator].capacity:
                arena_iterator += 1
                nmpt_iterator = 0
                if arena_iterator >= len(arenas):
                    arena_iterator = 0
                    starting_time += tournament.event.match_time 
            match.round = k+1
            match.save()
    return HttpResponseRedirect(reverse("competitions:round_robin_tournament", args=(tournament_id,)))
    #still have a little bit of confusion with the ordering of matches.


def generate_round_robin_rankings(request, tournament_id):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    team_wins = {team: 0 for team in tournament.teams.all()}
    matches = tournament.match_set.all()
    for match in matches:
        if match.advancers.all().count > 1:
            for team in match.advancers.all():
                team_wins[team] += tournament.points_per_tie
        else:
            for team in match.advancers.all():
                team_wins[team] += tournament.points_per_win
    sorted_team_wins = dict(sorted(team_wins.items(), key=lambda x:x[1]))
    i = len(sorted_team_wins)
    for i, kv in zip(range(len(sorted_team_wins), 1), sorted_team_wins.items()):
        key = kv[0]
        rank = Ranking.objects.create(tournament=tournament, team=key, rank=i)
        rank.save()
    pass

def home(request: HttpRequest):
    return render(request, "competitions/home.html")

def tournament(request: HttpRequest, tournament_id: int):
    tournament = get_tournament(request, tournament_id)
    if not tournament.match_set.exists():   
        return generate_tournament_matches(request, tournament_id)
    if isinstance(tournament, SingleEliminationTournament):
        #return HttpResponseRedirect(reverse("competitions:single_elimination_tournament", args=(tournament_id,)))
        return single_elimination_tournament(request, tournament_id)
    elif isinstance(tournament, RoundRobinTournament):
        #return HttpResponseRedirect(reverse("competitions:round_robin_tournament", args=(tournament_id,)))
        return round_robin_tournament(request, tournament_id)
    raise Http404

@login_required
def create_tournament(request: HttpRequest):
    tournament_type = request.GET.get('tournament_type', None)
    if not tournament_type:
        return render(request, "competitions/create_tournament.html")
    tournament_type = str(tournament_type).lower().strip()

    if tournament_type == 'rr':
        FORM_CLASS = CreateRRTournamentForm
    elif tournament_type == 'se':
        FORM_CLASS = CreateSETournamentForm
    else:
        raise BadRequest

    if request.method == 'POST':
        form = FORM_CLASS(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("competitions:tournament", args=(form.instance.id,)))

    form = FORM_CLASS()
    return render(request, "competitions/create_tournament_form.html", {"form": form, "tournament_type": tournament_type})

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

    bracket_array = []
    def generate_competitor_data(team, prev, match):
        is_next = match.next_matches.exists()
        connector = None
        if is_next:
            queryset = match.next_matches.all()[0].prev_matches.all()
            midpoint = (queryset.count() - 1) / 2
            index = list(queryset).index(match)
            # diff = abs(index - midpoint)
            connector = "connector-down" if index < midpoint else "connector-up" if index > midpoint else "connector-straight"

        return {
            "name": team.name if team else "TBD",
            "won": team in match.advancers.all(),
            "is_next": is_next,
            "prev": prev and team,
            "match_id": match.id,
            "connector": connector,
            # "connector_multiplier": 0
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
                #if i = 1, add another dummy match above/below?
        else:
            if len(bracket_array) <= curr_round+1:
                bracket_array.append({})
            bracket_array[curr_round+1][base_index] = None

    read_tree_from_node(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True).first(), 0, 0)

    bracket_array.pop()

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
    redirect_to = request.GET.get('next', '')
    redirect_id = request.GET.get('id', None)
    if redirect_id:
        redirect_id = [redirect_id]
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    if request.method == 'POST':
        form = RRTournamentStatusForm(request.POST)
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
    numRounds = tournament.num_rounds
    bracket_array =  [{i:[]} for i in range(numRounds)]
    for i in range(numRounds):
        rounds = sorted([match for match in Match.objects.filter(tournament=tournament, round=i+1)], key=lambda match : match.arena.id)
        for j in range(len(rounds)):
            team_data = []
            won = False
            is_next = True
            prev = False
            connector = None
            k = 0
            for team in rounds[j].starting_teams.all():
                if team in rounds[j].advancers.all():
                    won = True
                team_data.append({'name': team.name, 'won': won, 'is_next': is_next, 'prev': prev, 'match': rounds[j], 'connector': connector})
                won = False
                k += 1
            for q in range(k, tournament.teams_per_match):
                team_data.append({'name': 'TBD', 'won': won, 'is_next': is_next, 'prev': prev, 'match': rounds[j], 'connector': connector})
            bracket_array[i][j] = team_data
    
    num_matches = len(bracket_array)/numRounds
    mostTeamsInRound = tournament.teams_per_match

    round_data = []
    matchWidth, connectorWidth, teamHeight = 200, 25, 25
    bracketWidth = (matchWidth + (connectorWidth * 2)) * numRounds
    bracketHeight = mostTeamsInRound * 50
    roundWidth = matchWidth + connectorWidth

    for round_matches in reversed(bracket_array):
        match_height = bracketHeight / num_matches
        match_data = []

        for team_data in round_matches.values():
            num_teams = mostTeamsInRound if team_data else 0
            center_height = teamHeight * num_teams
            center_top_margin = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "center_top_margin": center_top_margin,
                "arena": team_data[0].get('match').arena
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
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    context = {"tournament": tournament, "bracket_dict": bracket_dict}
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
            if redirect_id:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
            elif redirect_to:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                # if we don't know where they came from, just send them to the competition page
                return HttpResponseRedirect(reverse(f"competitions:competition", args=[competition_id]))
    if competition.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    if Match.objects.filter(next_matches__isnull=True).filter(tournament__competition=competition_id).exists():
        winner = Match.objects.filter(next_matches__isnull=True).filter(tournament__competition=competition_id).first().advancers.all()
    else:
        winner = None
    context = {
        "competition": competition, 
        "form": SETournamentStatusForm(), 
        "winner": winner,
    }
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


def user_profile(request, profile_id):
    context = {
        'user': User.objects.filter(profile__id = profile_id).first(),
        'profile': Profile.objects.filter(id = profile_id).first(),
    }
    return render(request, 'competitions/user_profile.html', context)


def competition_score_page(request, competition_id):
    selected_competition = Competition.objects.get(id = competition_id)
    ranked_tournaments = selected_competition.tournament_set.order_by("points")
    completed_tournaments = ranked_tournaments.filter(status = Status.COMPLETE)
    unsorted_total_scores_dictionary = dict()
    last_tournament_matches = dict()
    list_of_tournament_points = list()
    for team in selected_competition.teams.all():
        val = 0
        for completed_tournament in completed_tournaments.all():
            last_match = Match.objects.filter(tournament__id = completed_tournament.id, next_matches__isnull = True).first()
            if team in last_match.advancers.all():
                val = val + completed_tournament.points
        unsorted_total_scores_dictionary[team] = val
    for completed_tournament in completed_tournaments.all():
        last_match = Match.objects.filter(tournament__id = completed_tournament.id, next_matches__isnull = True).first()
        last_tournament_matches[last_match.advancers.first()] = completed_tournament.id
    list_of_sorted_team_tuples = [(k, v) for k, v in sorted(unsorted_total_scores_dictionary.items(), key=lambda item: item[1])]
    list_of_sorted_last_matches = [(k, v) for k, v in sorted(last_tournament_matches.items(), key=lambda item: item[1])]
    for k, v in list_of_sorted_last_matches:
        list_of_tournament_points.append((v, SingleEliminationTournament.objects.filter(id = v).first().points))
    context = {
        'competition': selected_competition,
        'completed_tournaments': completed_tournaments,
        'sorted_team_tuples': list_of_sorted_team_tuples,
        'last_matches': list_of_sorted_last_matches,
        'list_of_tournament_points': list_of_tournament_points,
    }
    return render(request, "competitions/comp_scoring.html", context)

def team(request: HttpRequest, team_id: int):
    today = timezone.now().date()
    upcoming_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id), tournament__competition__start_date__lte=today, tournament__competition__end_date__gte=today, advancers=None).order_by("-time")
    past_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id)).exclude(advancers=None).order_by("-time")
    past_matches_drawn = list()
    past_tournaments_won = list()
    past_matches_won_singly = list()
    past_matches_won = past_matches.filter(starting_teams__id = team_id, advancers__id = team_id).annotate(num_advancers = Count("advancers"))
    for past_match_won in past_matches_won:
        if past_match_won.advancers.count() == 1:
            past_matches_won_singly.append(past_match_won)
        else:
            past_matches_drawn.append(past_match_won)
    past_matches_lost = past_matches.exclude(advancers__id = team_id)
    past_tournaments = SingleEliminationTournament.objects.filter(teams__id = team_id, status = Status.COMPLETE).order_by("start_time")
    for past_tournament in past_tournaments:
        last_match_advancers = past_tournament.match_set.last().advancers.all()
        if Team.objects.filter(id = team_id) in last_match_advancers:
            past_tournaments_won.append(past_tournament)
    past_competitions = Competition.objects.filter(teams__id = team_id, status = Status.COMPLETE).order_by("end_date")    
    context = {
        'team': Team.objects.get(pk=team_id),
        'upcoming_matches': upcoming_matches,
        'won_matches': past_matches_won_singly,
        'past_matches': past_matches,
        'draw_matches': past_matches_drawn,
        'lost_matches': past_matches_lost,
        'won_tournaments': past_tournaments_won,
        'past_tournaments': past_tournaments,
        'past_competitions': past_competitions,
    }
    return render(request, "competitions/team.html", context)


def _raise_error_code(request: HttpRequest):
    try:
        error_code = int(request.GET.get('code', 0)) # type: ignore
    except:
        raise BadRequest

    if error_code == 403:
        raise PermissionDenied
    elif error_code == 404:
        raise Http404
    elif error_code == 500:
        raise Exception("This is a test 500 error.")
    else:
        return HttpResponse(status=error_code)

def set_timezone_view(request: HttpRequest):
    """Please leave this view at the bottom. Create any new views you need above this one"""
    if request.method == "POST":
        if request.POST["timezone"]:
            request.session["timezone"] = request.POST["timezone"]
            messages.success(request, f"Timezone set successfully to {request.POST['timezone']}.")
            return redirect("/")
        else:   
            messages.error(request, "Invalid timezone.")
    timezones = sorted(zoneinfo.available_timezones())
    return render(request, "timezones.html", {"timezones": timezones})
