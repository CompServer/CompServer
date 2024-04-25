from datetime import datetime
import math
import random
from typing import Dict, Set, Union
import zoneinfo

from django.contrib import messages
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.core.exceptions import SuspiciousOperation
from django.db.models import Q, QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template import RequestContext
from django.template.exceptions import TemplateDoesNotExist
from django.urls import reverse
from django.utils import timezone
from crispy_forms.utils import render_crispy_form

from .forms import *
from .models import *
from .utils import *

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

def generate_single_elimination_matches(request, tournament_id: int):
    #sort the list by ranking, then use a two-pointer alogrithm to make the starting matches
    tournament: SingleEliminationTournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    arena_iterator = 0
    nmpt_iterator = 0
    arenas = [i for i in tournament.competition.arenas.filter(is_available=True)]
    if not arenas:
        raise SuspiciousOperation("No arenas available for this competition.")
    starting_time = tournament.start_time 
    team_ranks = []
    if tournament.prev_tournament == None:
        for i, team in enumerate(tournament.teams.all()):
            rank = Ranking.objects.create(tournament=tournament, team=team, rank=i+1)
            rank.save()
            team_ranks = sorted([(rank.team, rank.rank) for rank in tournament.ranking_set.all()], key=lambda x: x[1])
    elif not tournament.prev_tournament.ranking_set.exists():
        generate_round_robin_rankings(tournament.prev_tournament.id)
        team_ranks = sorted([(rank.team, rank.rank) for rank in tournament.prev_tournament.ranking_set.all()], key=lambda x: x[1])
    elif  tournament.prev_tournament.ranking_set.exists():
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
                starting_time += tournament.event.match_time
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

def isPlayed(teams_played: Set[Team], match_teams: QuerySet[Team]):
    return any([team in teams_played for team in match_teams])

def generate_round_robin_matches(request, tournament_id):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    arena_iterator = 0
    nmpt_iterator = 0
    arenas = [i for i in tournament.competition.arenas.filter(is_available=True)]
    starting_time = tournament.start_time 
    teams = [team for team in tournament.teams.all()]
    teams_played = {team: set() for team in teams}
    for team in teams:
        if team == teams[len(teams)-1]:
            break
        for k in range(tournament.matches_per_team):
            if len(teams_played[team]) >= tournament.matches_per_team:
                break
            match = Match.objects.create(tournament=tournament)
            match.starting_teams.add(team)
            for i in range(1, tournament.teams_per_match):
                j = random.randint(0, len(teams)-1)
                while(teams[j] in match.starting_teams.all() or \
                isPlayed(teams_played[teams[j]], match.starting_teams.all()) or \
                    len(teams_played[teams[j]]) >= tournament.matches_per_team):
                    j = random.randint(0, len(teams)-1)    
                match.starting_teams.add(teams[j])
            for team in match.starting_teams.all():
                for team2 in match.starting_teams.all():
                    if team != team2:
                        teams_played[team].add(team2)
            match.save()
    matches = [match for match in tournament.match_set.all()]
    round_num = 1
    curr_round = []
    num_participated = [0 for _ in range(len(matches))]
    while num_participated != [1 for _ in range(len(matches))]:
        j = random.randint(0, len(matches)-1)
        while num_participated[j] == 1:
            j = random.randint(0, len(matches)-1)
        num_participated[j] = 1    
        matches[j].time = starting_time
        matches[j].arena = arenas[arena_iterator]
        matches[j].round_num = round_num
        matches[j].save()
        curr_round.append(matches[j])
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time 
                round_num += 1
                curr_round = []
    return HttpResponseRedirect(reverse("competitions:round_robin_tournament", args=(tournament_id,)))
    #still have a little bit of confusion with the ordering of matches.

def get_points(tournament_id: int):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    team_wins = {team: 0 for team in tournament.teams.all()}
    matches = tournament.match_set.all()
    for match in matches:
        if not match.advancers.exists():
            continue
        if match.advancers.all().count() > 1:
            for team in match.advancers.all():
                team_wins[team] += tournament.points_per_tie
        else:
            for team in match.advancers.all():
                team_wins[team] += tournament.points_per_win
        for team in match.starting_teams.all():
            if team not in match.advancers.all():
                team_wins[team] += tournament.points_per_loss
    return team_wins

def generate_round_robin_rankings(tournament_id: int):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    team_wins = get_points(tournament_id)
    sorted_team_wins = dict(sorted(team_wins.items(), key=lambda x:x[1], reverse=True))
    for i, kv in zip(range(1, len(sorted_team_wins)+1), sorted_team_wins.items()):
        key = kv[0]
        rank = Ranking.objects.create(tournament=tournament, team=key, rank=i)
        rank.save()
    pass

def swap_matches(request: HttpRequest, tournament_id: int):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    form = None
    if request.method == 'POST':
        form = TournamentSwapForm(request.POST, tournament=tournament)
        if form.is_valid():
            team1 = form.cleaned_data.get('team1')
            team2 = form.cleaned_data.get('team2')
            round_num = form.cleaned_data.get('round_num')
            if round_num < 1 or not Match.objects.filter(tournament=tournament, round_num=round_num).exists():
                #print("Invalid round")
                return HttpResponseRedirect(reverse("competitions:swap_matches", args=(tournament_id,)))
            match1 = Match.objects.filter(tournament=tournament, starting_teams__in=[team1.id], round_num=round_num).first()
            match2 = Match.objects.filter(tournament=tournament, starting_teams__in=[team2.id], round_num=round_num).first()
            #print(match1, match2)
            match1.starting_teams.remove(team1)
            match2.starting_teams.remove(team2)
            match1.starting_teams.add(team2)
            match2.starting_teams.add(team1) 
            match1.save()
            match2.save()
            #print(match1, match2)
            messages.success(request, "Teams swapped successfully.")
            return HttpResponseRedirect(reverse("competitions:tournament", args=(tournament_id,)))
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    if not form:
        form = TournamentSwapForm(tournament=tournament)
    return render(request, "competitions/swap_matches.html", {"form": form})

def home(request: HttpRequest):
    return render(request, "competitions/home.html")

def tournament(request: HttpRequest, tournament_id: int):
    #generate_matches = request.GET.get('generate_matches', True)

    tournament = get_tournament(request, tournament_id)

    if not tournament.match_set.exists(): #and generate_matches:
        return generate_tournament_matches(request, tournament_id)

    if isinstance(tournament, SingleEliminationTournament):
        #return HttpResponseRedirect(reverse("competitions:single_elimination_tournament", args=(tournament_id,)))
        return single_elimination_tournament(request, tournament_id)
    elif isinstance(tournament, RoundRobinTournament):
        #return HttpResponseRedirect(reverse("competitions:round_robin_tournament", args=(tournament_id,)))
        return round_robin_tournament(request, tournament_id)
    raise Http404

# @login_required
# def create_tournament(request: HttpRequest):
#     competition_id = request.GET.get('competition_id',None)
#     tournament_type = request.GET.get('tournament_type', None)

#     if competition_id is None:
#         messages.error(request, "No competition selected.")
#         return HttpResponseRedirect(reverse("competitions:competitions"))
#     try:
#         competition = get_object_or_404(Competition, pk=int(competition_id))
#     except:
#         messages.error(request, "Invalid competition.")
#         return HttpResponseRedirect(reverse("competitions:competitions"))
    
#     if not tournament_type:
#         return render(request, "competitions/create_tournament.html", context={"competition": competition})
    
#     tournament_type = str(tournament_type).lower().strip()

#     if tournament_type == 'rr':
#         FORM_CLASS = RRTournamentForm
#     elif tournament_type == 'se':
#         FORM_CLASS = SETournamentForm
#     else:
#         raise SuspiciousOperation

#     form = None
#     if request.method == 'POST':
#         form = FORM_CLASS(request.POST, competition=competition)
#         if form.is_valid():
#             form.full_clean()
#             instance = form.save(commit=False)
#             instance.competition = competition
#             instance.save()
#             form.save() # may not work?
#             return HttpResponseRedirect(f"{reverse('competitions:tournament', args=(form.instance.id,))}")
#         else:
#             for error_field, error_desc in form.errors.items():
#                 form.add_error(error_field, error_desc)
#     if not form:
#         form = FORM_CLASS(competition=competition)
#     return render(request, "FORM_BASE.html", {'form_title': "Create Tournament", 'action': f"?tournament_type={tournament_type}&competition_id={competition.id}" , "form": form,  "form_submit_text": "Create"})

@login_required
def create_tournament_htmx(request: HttpRequest):
    competition_id = request.GET.get('competition_id',None)
    #tournament_type = str(request.GET.get('tournament_type','')).lower().strip()

    # if tournament_type == 'rr':
    #     FORM_CLASS = RRTournamentForm
    # elif tournament_type == 'se':
    #     FORM_CLASS = SETournamentForm
    # else:
    #     raise SuspiciousOperation
    
    competition = get_object_or_404(Competition, pk=competition_id)
    
    form = None
    if request.method == 'POST':
        form = FORM_CLASS(request.POST, competition=competition)
        if form.is_valid():
            form.full_clean()
            instance = form.save(commit=False)
            instance.competition = competition
            instance.save()
            form.save() # may not work?
            return HttpResponseRedirect(f"{reverse('competitions:tournament', args=(form.instance.id,))}")
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    # if not form:
    #     form = FORM_CLASS(competition=competition)

    form = TournamentTypeSelectForm(competition_id=competition.id)
    form_html = render_crispy_form(form, helper=form.helper)

    return render(request, "competitions/new_tournament_form.html", RequestContext(request, {"form_html": form_html, "action": "", "form_submit_text": "Select", "form_title": "Create"}).flatten())

@login_required
def edit_tournament(request: HttpRequest, tournament_id: int):
    tournament = get_tournament(request, tournament_id)
    if isinstance(tournament, SingleEliminationTournament):
        FORM_CLASS = SETournamentForm
    elif isinstance(tournament, RoundRobinTournament):
        FORM_CLASS = RRTournamentForm
    else:
        raise Http404

    form = None
    if request.method == 'POST':
        form = FORM_CLASS(request.POST, instance=tournament, competition=tournament.competition)
        if form.is_valid():
            form.save() # may not work?
            return HttpResponseRedirect(f"{reverse('competitions:tournament', args=(form.instance.id,))}")
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    if not form:
        form = FORM_CLASS(instance=tournament, competition=tournament.competition)
    return render(request, "FORM_BASE.html", {'form_title': "Edit Tournament", 'action': f"" , "form": form,  "form_submit_text": "Edit"})

@login_required
def arena_color(request: HttpRequest, competition_id: int):
    competition = get_object_or_404(Competition, pk=competition_id)
    form = None
    if request.method == 'POST':
        form = ArenaColorForm(request.POST, competition=competition)
        if form.is_valid():
            arena = form.cleaned_data.get('arena')
            color = form.cleaned_data.get('color')
            arena.color = color
            arena.save()
            messages.success(request, "Color changed successfully.")
            return HttpResponseRedirect(reverse('competitions:competition', args=(competition_id,)))
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    if not form:
        form = ArenaColorForm(competition=competition)
    return render(request, "competitions/arena_color.html", {'form': form})

def single_elimination_tournament(request: HttpRequest, tournament_id: int):
    redirect_to = request.GET.get('next', '')
    redirect_id = request.GET.get('id', None)
    if redirect_id:
        redirect_id = [redirect_id]
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    if request.method == 'POST':
        form = TournamentStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            tournament.status = status
            tournament.save()
            messages.success(request, "Status changed successfully.")
            if redirect_id == None:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
    if tournament.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))

    # -----VARIABLES-----
    bracket_array = []
    matchWidth = 175
    connectorWidth = 50
    teamHeight = 25
    roundWidth = matchWidth + connectorWidth
    # -------------------

    def generate_competitor_data(match):
        output = []

        is_next = match.next_matches.exists()
        curr_match_teams = match.get_competing_teams()
        
        for team in curr_match_teams:
            output.append({
                "name": team.name if team else "TBD",
                "won": team in match.advancers.all(),
                "is_next": is_next,
                "match_id": match.id,
                "team_id": team.id
            })
        return output
    
    def generate_connector_data(match):
        is_next = match.next_matches.exists()
        if not is_next:
            return {
                "connector": None,
                "team_index_offset": None,
                "match_offset_mult": None,
                "connector_width_actual": None,
                "team_index_offset_mult": None,
            }

        curr_match_teams = match.get_competing_teams()

        next_match = match.next_matches.all().first()
        feed_matches = next_match.prev_matches.all()
        num_feed_matches = feed_matches.count()
        midpoint_index = (num_feed_matches - 1) / 2
        match_index = list(feed_matches).index(match)
        num_divisions = max(math.floor(num_feed_matches/2),1)

        if (abs(match_index - midpoint_index) <= 1):
            match_offset_mult = abs(match_index - midpoint_index)
            connector_width_actual = (1*connectorWidth)/(num_divisions+1)
        else:
            match_offset_mult = abs(match_index - midpoint_index)
            num_something_idk = math.floor(abs(match_index - midpoint_index) + 0.5)
            connector_width_actual = (num_something_idk*connectorWidth)/(num_divisions+1)

        
        next_match_teams = next_match.get_competing_teams()
        from_index = len(curr_match_teams)/2
        to_index =  match_index
        winner = False
        winner_id = None
        
        for index, team in enumerate(curr_match_teams):
            if is_next and team in match.advancers.all():
                to_index = next_match_teams.index(team)
                from_index = index
                winner = True
                winner_id = team.id

        if match_index <= midpoint_index:
            index_diff = to_index-from_index
            len_diff = (len(curr_match_teams)-len(next_match_teams))/2 
            vertical_margin = teamHeight*(from_index+0.5)
            connector = "connector-down"
            if not winner:
                index_diff += 0.5
                vertical_margin -= (teamHeight/2)
        else:
            index_diff = from_index-to_index
            len_diff = (len(next_match_teams)-len(curr_match_teams))/2
            vertical_margin = teamHeight*(len(curr_match_teams)-from_index-0.5)
            connector = "connector-up"
            if not winner:
                index_diff += 0.5
                vertical_margin += (teamHeight/2)

        team_index_offset_mult = index_diff+len_diff
        team_index_offset = team_index_offset_mult*teamHeight

        return{
            "connector": connector,
            "team_index_offset": team_index_offset,
            "match_offset_mult": match_offset_mult,
            "connector_width_actual": connector_width_actual,
            "team_index_offset_mult": team_index_offset_mult,
            "vertical_margin": vertical_margin,
            "winner_id": winner_id
        }
    
    def read_tree_from_node(curr_match, curr_round, base_index):
        if len(bracket_array) <= curr_round:
            bracket_array.append({})

        bracket_array[curr_round][base_index] = [generate_competitor_data(curr_match), generate_connector_data(curr_match)]
        
        prevs = curr_match.prev_matches.all()
        if prevs:
            for i, prev in enumerate(prevs):
                read_tree_from_node(prev, curr_round+1, 2*base_index+i)
        else:
            if len(bracket_array) <= curr_round+1:
                bracket_array.append({})
            bracket_array[curr_round+1][base_index] = None

    read_tree_from_node(Match.objects.filter(tournament=tournament_id, next_matches__isnull=True).first(), 0, 0)

    bracket_array.pop()

    numRounds = len(bracket_array)

    mostTeamsInRound = max(sum(len(teams[0]) if teams else 0 for teams in round.values()) for round in bracket_array)

    round_data = []

    bracketWidth = (matchWidth + connectorWidth ) * numRounds
    bracketHeight = mostTeamsInRound * 50

    for round_matches in reversed(bracket_array):
        num_matches = len(round_matches)
        match_height = bracketHeight / num_matches
        final_match_data = []

        for generated_match_data in round_matches.values():
            if not generated_match_data:
                continue
            num_teams = len(generated_match_data[0]) if generated_match_data else 0
            if num_teams > tournament.teams_per_match:
                messages.error(request, "Invalid number of teams per match.")
            center_height = teamHeight * num_teams
            center_top_margin = (match_height - center_height) / 2

            final_match_data.append({
                "team_data": generated_match_data[0],
                "connector_data": generated_match_data[1],
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "center_top_margin": center_top_margin,
            })

        round_data.append({"match_data": final_match_data})


    bracket_dict = {
        "bracketWidth": bracketWidth, 
        "bracketHeight": bracketHeight, 
        "roundWidth": roundWidth, 
        "roundHeight": bracketHeight,
        "teamHeight": teamHeight,
        "connectorWidth": connectorWidth,
        "round_data": round_data,
        "team_height": teamHeight,
    }
    
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    context = {"tournament": tournament, "bracket_dict": bracket_dict, "form": TournamentStatusForm()}
    return render(request, "competitions/bracket.html", context)

def round_robin_tournament(request: HttpRequest, tournament_id: int):
    redirect_to = request.GET.get('next', '')
    redirect_id = request.GET.get('id', None)
    if redirect_id:
        redirect_id = [redirect_id]
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    if request.method == 'POST':
        form = TournamentStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            tournament.status = status
            tournament.save()
            messages.success(request, "Status changed successfully.")
            if redirect_id == None:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
    if tournament.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    numRounds = tournament.match_set.order_by('-round_num').first().round_num
    bracket_array =  [{i:[]} for i in range(numRounds)]
    for i in range(numRounds):
        rounds = sorted([match for match in Match.objects.filter(tournament=tournament, round_num=i+1)], key=lambda match : (match.arena.id, match.time))
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
            for _ in range(k, tournament.teams_per_match):
                team_data.append({'name': 'No Team', 'won': won, 'is_next': is_next, 'prev': prev, 'match': rounds[j], 'connector': connector})
            bracket_array[i][j] = team_data
    
    num_matches = len(bracket_array)/numRounds
    mostTeamsInRound = tournament.teams_per_match

    round_data = []
    matchWidth, connectorWidth, teamHeight = 200, 25, 25
    bracketWidth = (matchWidth + (connectorWidth * 2)) * numRounds
    bracketHeight = mostTeamsInRound * 50
    roundWidth = matchWidth + connectorWidth

    for round_matches in bracket_array:
        match_height = bracketHeight / num_matches
        match_data = []

        for team_data in round_matches.values():
            if team_data == []:
                continue
            num_teams = mostTeamsInRound if team_data else 0
            center_height = teamHeight * num_teams
            center_top_margin = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "center_top_margin": center_top_margin,
                "arena": team_data[0].get('match').arena,
                "match":  team_data[0].get('match'),
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
    team_wins = get_points(tournament_id)
    winning_points = max(team_wins.values())
    winning_teams = [team for team in team_wins if team_wins[team] == winning_points]
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    context = {"tournament": tournament, "bracket_dict": bracket_dict, "team_wins": team_wins, "winning_teams": winning_teams, "form": TournamentStatusForm()}
    return render(request, "competitions/round_robin_tournament.html", context)

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
            messages.success(request, "Status changed successfully.")
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
        "form": TournamentStatusForm(), 
        "winner": winner,
    }
    return render(request, "competitions/competition.html", context)

@login_required
def create_competition(request: HttpRequest):
    # sport_id = request.GET.get('sport', None)
    # if sport_id is None:
    #     return render(request, "competitions/create_competition.html", {"sports": Sport.objects.all()})
    # try:
    #     sport_id = int(sport_id)
    # except:
    #     raise Http404("Not a valid sport.")
    # sport = get_object_or_404(Sport, pk=sport_id)

    form = None
    if request.method == 'POST':
        form = CreateCompetitionsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Competition created successfully.")
            return HttpResponseRedirect(reverse("competitions:competition", args=(form.instance.id,)))
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    if not form:
        form = CreateCompetitionsForm()
    #form_html = render_crispy_form(form)
    return render(request, "competitions/create_competition_form.html", {"form": form}) #{"form_html": form_html})

def credits(request: HttpRequest):
    return render(request, "competitions/credits.html")

@login_required
def judge_match(request: HttpRequest, match_id: int):
    instance: Match = get_object_or_404(Match, pk=match_id)
    user = request.user

    tournament: AbstractTournament = instance.tournament
    assert isinstance(tournament, AbstractTournament)
    competetion: Competition = tournament.competition
    assert isinstance(competetion, Competition)
    
    if not competetion.is_judgable or not tournament.is_judgable:
        messages.error(request, "This match is not judgable: Both the competition and tournament must be set to Open.")
        #print("This match is not judgable.")
        raise SuspiciousOperation("This match is not judgable.")
    # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
    if not (user in tournament.judges.all() \
    or user in competetion.plenary_judges.all() \
    or user.is_superuser):
        messages.error(request, "You are not authorized to judge this match.")
        #print("You are not authorized to judge this match.")
        raise PermissionDenied("You are not authorized to judge this match.")
        #return HttpResponseRedirect(reverse('competitions:competition', args=[competetion.id]))

    winner_choices = []
    if instance.starting_teams.exists() and instance.prev_matches.exists():
        winner_choice_ids = []
        for match in instance.prev_matches.all():
            if match.advancers.exists():
                winner_choice_ids.extend([x.id for x in match.advancers.all()])
            else:
                messages.error(request, "One or more previous matches have not been judged.")
                #print("One or more previous matches have not been judged.")
                raise SuspiciousOperation("One or more previous matches have not been judged.")
                #return HttpResponse(, reason="One or more previous matches have not been judged.")
        winner_choice_ids.extend([x.id for x in instance.starting_teams.all()])
        winner_choices = Team.objects.filter(id__in=winner_choice_ids)
    elif instance.prev_matches.exists():
        winner_choice_ids = []
        for match in instance.prev_matches.all():
            if match.advancers.exists():
                winner_choice_ids.extend([x.id for x in match.advancers.all()])
            else:
                messages.error(request, "One or more previous matches have not been judged.")
                #print("One or more previous matches have not been judged.")r
                raise SuspiciousOperation("One or more previous matches have not been judged.")
                #return HttpResponse(, reason="One or more previous matches have not been judged.")
        winner_choices = Team.objects.filter(id__in=winner_choice_ids)
    elif instance.starting_teams.exists():
        winner_choices = instance.starting_teams.all()
    else:
        messages.error(request, "This match has no starting teams or previous matches.")
        #print("This match has no starting teams or previous matches.")
        raise SuspiciousOperation("This match has no starting teams or previous matches.")
    
    # if instance.next_match is not None and instance.next_match.advancers.exists():
    #         messages.error(request, "The winner of the next match has already been decided.")
    #         #print("This match has already been judged.")
    #         return HttpResponseRedirect(reverse('competitions:tournament', args=[instance.tournament.id]))
    form = None
    if request.method == 'POST':
        form = JudgeForm(request.POST, instance=instance, possible_advancers=winner_choices)
        if form.is_valid():
            form.save()
            messages.success(request, "Match judged successfully.")
            #print("Match judged successfully.")
            return HttpResponseRedirect(reverse('competitions:tournament', args=[instance.tournament.id]))
        # else:
        #     for error_field, error_desc in form.errors.items():
        #         form.add_error(error_field, error_desc)
    if not form:
        form = JudgeForm(instance=instance, possible_advancers=winner_choices)
    return render(request, 'competitions/match_judge.html', {'form': form, 'match': instance, "teams": winner_choices})

def profile(request, user_id):
    #check admin
    #check coach
    if Coach.objects.filter(id = user_id).exists():
        teams_coached = Team.objects.filter(coach_id = user_id)
        team_records = []
        wins = 0
        losses = 0
        for team_coached in teams_coached:
            past_matches = Match.objects.filter(starting_teams=team_coached)#add a part about time and ordering)
            for match in past_matches:
                if team_coached in match.advancers:
                    wins = wins + 1
                else:
                    losses = lossess + 1
            team_records.append((team_coached, wins, losses))
        #current coaching competitions
        # see collection of forms
    #admin
    #coach
    #judge
    #competitors
    #spectatotr
    user = User.objects.filter(id = user_id).first()
    context = {
        'user': user,
        'profile': Profile.objects.filter(id = user.profile_id).first(),
    }
    request.user.is_authenticated
    return render(request, 'competitions/user_profile.html', context)

def results(request, competition_id):
    competition = Competition.objects.get(id = competition_id)
    tournaments = competition.tournament_set.order_by("points").filter(status = Status.COMPLETE)
    tournament_names = []
    tournament_names = [tournament.event.name for tournament in tournaments]
    team_names = []
    team_names = [team.name for team in competition.teams.order_by("name")]
    totals = []
    tournament_scorings = {}
    for tournament in tournaments:
        scores = []
        last_match = Match.objects.filter(tournament__id = tournament.id, next_matches__isnull = True).first()
        winners = last_match.advancers.all()
        for team_name in team_names:
            team = Team.objects.filter(name=team_name).first()
            if team in winners:
                scores.append(float(tournament.points))
            else:
                scores.append(0)
        tournament_scorings[tournament.event.name] = scores
    team_scorings = []
    for team_name in team_names:
        team = Team.objects.filter(name=team_name).first()
        scores = []
        for tournament in tournaments:
            last_match = Match.objects.filter(tournament__id = tournament.id, next_matches__isnull = True).first()
            if team in last_match.advancers.all():
                scores.append(tournament.points)
            else:
                scores.append(0)
        score_total = sum(scores)
        totals.append((team_name, score_total))
        team_scorings.append((scores))
    judge_names = [plenary_judge.first_name + " " + plenary_judge.last_name for plenary_judge in competition.plenary_judges.order_by("-username")]
    context = {
        'tournament_scorings': tournament_scorings,
        'tournament_names': tournament_names,
        'team_names': team_names,
        'competition': competition,
        'tournaments': tournaments,
        'team_scorings': team_scorings,
        'judge_names': judge_names,
        'team_and_total': totals,
    }
    return render(request, "competitions/results.html", context)

def team(request: HttpRequest, team_id: int):
    team = Team.objects.filter(id=team_id).first()
    today = timezone.now().date()
    upcoming_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id), tournament__competition__start_date__lte=today, tournament__competition__end_date__gte=today, advancers=None).order_by("-time")
    past_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id)).exclude(advancers=None).order_by("-time")
    past_competitions = Competition.objects.filter(teams__id = team_id, status = Status.COMPLETE).order_by("end_date")
    past_tournaments_won = []
    past_tournaments = SingleEliminationTournament.objects.filter(teams__id = team_id, status = Status.COMPLETE).order_by("start_time")
    for past_tournament in past_tournaments:
        last_match_advancers = past_tournament.match_set.last().advancers.all()
        if team in last_match_advancers:
            past_tournaments_won.append(past_tournament)
    losses = []
    wins = []
    draws = []
    for pm in past_matches:
        first_half = " in Round " + str(pm.round_num) + " in "
        second_half = " tournament @" + pm.tournament.competition.name
        num_starting_teams = pm.starting_teams.count()
        num_advancers = pm.advancers.count()
        if num_starting_teams == 1 and pm.starting_teams.all().first().id == team_id and pm.advancers.all().first().id == team_id:
            wins.append((("Granted a BYE" + first_half), pm.tournament, second_half))
        else:
            starting_teams_names = []
            for starting_team in pm.starting_teams.all():
                if starting_team.id != team_id:
                    starting_teams_names.append(starting_team.name)
            if num_advancers == 1 and pm.advancers.all().first().id == team_id:
                if num_starting_teams == 2:
                    wins.append((("Won against " + starting_teams_names.__getitem__(0) + first_half), pm.tournament, second_half))
                else:
                    wins.append((("Won against " + ",".join(starting_teams_names) + first_half), pm.tournament, second_half))
            else:
                advancer_team_ids = []
                advancer_teams_names = []
                for advancer in pm.advancers.all():
                    advancer_team_ids.append(advancer.id)
                    if advancer.id != team_id:
                        advancer_teams_names.append(advancer.name)
                if num_advancers > 1 and team_id in advancer_team_ids:
                    if num_advancers == 2:
                        draws.append((("Drew with " + "".join(advancer_teams_names) + first_half), pm.tournament, second_half))
                    else:
                        draws.append((("Drew with " + ",".join(advancer_teams_names) + first_half), pm.tournament, second_half))
                else:
                    if num_advancers == 2:
                        losses.append((("Lost against " + "".join(advancer_teams_names) + first_half), pm.tournament, second_half))
                    else:
                        losses.append((("Lost against " + ",".join(advancer_teams_names) + first_half), pm.tournament, second_half))
    context = {
        'team': team,
        'upcoming_matches': upcoming_matches,
        'wins': wins,
        'past_matches': past_matches,
        'draws': draws,
        'losses': losses,
        'won_tournaments': past_tournaments_won,
        'past_tournaments': past_tournaments,
        'past_competitions': past_competitions,
    }
    return render(request, "competitions/team.html", context)

def _raise_error_code(request: HttpRequest):
    try:
        error_code = int(request.GET.get('code', 0)) # type: ignore
    except:
        raise SuspiciousOperation

    # if error_code == 403:
    #     raise PermissionDenied
    # elif error_code == 404:
    #     raise Http404
    # else:
    try:
        return render(request, f'{error_code}.html', status=error_code)
    except TemplateDoesNotExist:
        try:
            return render(request, 'ERROR_BASE.html', context={"error_code": error_code, "error": f"{error_code} {http_codes.get(error_code, 'Unknown')}"}, status=error_code)
        except:
            return HttpResponse(status=error_code)

def not_implemented(request: HttpRequest, *args, **kwargs):
    """
    Base view for not implemented features. You can  use this view to show a message to the user that the feature is not yet implemented,
    or if you want to add a view for a URL to a page that doesn't exist yet.
    """
    messages.error(request, "This feature is not yet implemented.")
    #raise NotImplementedError()
    return render(request, 'skeleton.html')

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
