from datetime import datetime
import math

from django.contrib import messages
from django.core.exceptions import BadRequest
from django.shortcuts import render, get_object_or_404
import math, random
from .models import *
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
import random
import zoneinfo
from .models import *
from .forms import *

def is_overflowed(list1: list, num: int):
    for item in list1:
        if item < num:
            return False
    return True

def generate_single_elimination_matches(request, tournament_id):
    #sort the list by ranking, then use a two-pointer alogrithm to make the starting matches
    tournament = get_object_or_404(AbstractTournament, pk=tournament_id)
    # sort the teams by rank
    team_ranks = sorted([(rank.team, rank.rank) for rank in tournament.ranking_set.all()],key=lambda x: x[1])
    #sort_list(teams, ranks)
    rank_teams = {}
    for i in range(len(rank_teams)):
        rank_teams[i+1] = team_ranks[i][0]
    num_teams = len(rank_teams)
    num_matches, i = 1, 1
    extra_matches = []
    while num_matches * 2 < num_teams:
        num_matches *= 2
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
    matches.extend(new_matches)
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


def home(request):
    return render(request, "competitions/home.html")


def single_elimination_tournament(request: HttpRequest, tournament_id):
    '''
    This view is responsible for drawing the tournament bracket, it does this by:
    1) Recursively get all matches and put them in a 4d array
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
        if curr_match.starting_teams.exists():
            for team in curr_match.starting_teams.all():
                competitors.append({"name": team.name, "won": team in curr_match.advancers.all(), "prev":False, "match_id": curr_match.id}) 
        if curr_match.prev_matches.exists():
            for prev_match in curr_match.prev_matches.all():
                if prev_match.advancers.exists():
                    for team in prev_match.advancers.all():
                        competitors.append({"name": team.name, "won": team in curr_match.advancers.all(), "prev": True, "match_id": curr_match.id}) 
                else:
                    competitors.append({"name": "TBD", "won": False, "prev": False, "match_id": curr_match.id}) 

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
        else:
            # this fixes one off preliminary matches, but also creates a weird empty round which gets adressed later
            if len(bracket_array) <= curr_round+1:
                bracket_array.append({})
            bracket_array[curr_round+1][base_index] = None

    #mutates bracket_array
    read_tree_from_node(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True)[0], 0, 0)

    #this gets weird of the weird empty round caused by the previous section
    bracket_array.pop()

    bracket_array

    #the number of rounds in the tournament: top 8, semi-finals, championship, etc
    numRounds = len(bracket_array)

    #find the most number of teams in a single round, used for setting the height
    mostTeamsInRound = 0
    for round in bracket_array:
        teams_count = sum((len(teams) if teams is not None else 0) for teams in round.values())
        if teams_count > mostTeamsInRound:
            mostTeamsInRound = teams_count

    # _data means it contains the actual stuff to be displayed
    # everything else is just css styling or not passed
    # most variables are exactly what they sound like
    # you can also look at bracket.html to see how its used
    round_data = []
    matchWidth = 200
    connectorWidth = 25
    bracketWidth = (matchWidth+(connectorWidth*2))*numRounds
    bracketHeight = mostTeamsInRound*50
    roundWidth = matchWidth+connectorWidth

    for i in range(numRounds):
        num_matches = len(bracket_array[numRounds-i-1])
        match_height = bracketHeight / num_matches
        match_data = []
        for j in range(num_matches):
            team_data = []
            #this is where we convert from bracket_array (made above) to bracket_dict (used in template)
            num_teams = 0
            if j in bracket_array[numRounds-i-1] and bracket_array[numRounds-i-1][j] is not None:
                num_teams = len(bracket_array[numRounds-i-1][j])
                team_data = [
                    bracket_array[numRounds-i-1][j][k] for k in range(num_teams)
                ]
            
            team_height = 25
            center_height = (team_height) * num_teams
            center_top_margin = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "center_top_margin": center_top_margin,
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
    
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    context = {
        "tournament": tournament, 
        "bracket_dict": bracket_dict,
    }
    return render(request, "competitions/bracket.html", context)


def tournaments(request):
    return render(request, "competitions/tournaments.html")

def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "form": CompetitionStatusForm()}
    return render(request, "competitions/competitions.html", context)


def competition(request, competition_id: int):
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

def credits(request):
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
def judge_match(request, match_id: int):
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

def competition_score_page(request, competition_id):
    selected_competition = Competition.objects.filter(id = competition_id)
    ranked_tournaments = selected_competition.tournament_set.order_by("points")
    total_team_rankings_dictionary = dict()
    for team in selected_competition.teams.all():
        val = 0
        for tournament in ranked_tournaments.all():
            val = val + Ranking.objects.get(tournament__id = tournament.id, team__id = team.id)
        team_name = team.name
        total_team_rankings_dictionary[team.name] = val
    sorted_total_team_rankings_dictionary = sorted(total_team_rankings_dictionary.items(), key=lambda x:x[1])
    list_of_team_names = list(sorted_total_team_rankings_dictionary.keys())[0]
    list_of_team_objects = list()
    for team_name in list_of_team_names:
        list_of_team_objects.append(Team.objects.get(mame = team_name))
    total_scores_for_each_team_dictionary = dict()
    for team in selected_competition.teams.all():
        val = 0
        for completed_tournament in completed_tournaments.all():
            if completed_tournament.advancers__id == team.id():
                val = val + completed_tournament.points
        team_name = team.name
        total_score = val
        total_scores_for_each_team_dictionary[team_name] = total_score
    context = {
        'competition': selected_competition,
        'ranked_teams': list_of_team_objects, 
        'ranked_tournaments': ranked_tournaments,
        'total_scores_for_each_team_dictionary': total_scores_for_each_team_dictionary,
    }
    return render(request, "competitions/comp_scoring.html", context)

def team(request, team_id):
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