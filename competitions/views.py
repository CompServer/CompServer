from django.contrib import messages
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
import random
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
import math
from .models import *
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import AccessMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from .forms import *

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


def home(request):
    return render(request, "competitions/home.html")

def single_elimination_tournament(request, tournament_id):
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
        if curr_match.starting_teams.exists():
            competitors += [(("[" + team.name + "]") if team in curr_match.advancers.all() else team.name) for team in curr_match.starting_teams.all()]
        if curr_match.prev_matches.exists():
            for prev_match in curr_match.prev_matches.all():
                if prev_match.advancers.exists():
                    competitors += [(("[" + team.name + "]") if team in curr_match.advancers.all() else team.name) for team in prev_match.advancers.all()]
                else:
                    competitors += ["TBD"]

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
            # this fixes one of preliminary matches, but also creates a weird empty round which gets adressed later
            if len(bracket_array) <= curr_round+1:
                bracket_array.append({})
            bracket_array[curr_round+1][base_index] = None

    #mutates bracket_array
    read_tree_from_node(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True)[0], 0, 0)

    #this gets weird of the weird empty round caused by the previous section
    bracket_array.pop()

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
    connectorWidth = 50
    bracketWidth = (matchWidth+connectorWidth)*numRounds
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
                    {"team_name": bracket_array[numRounds-i-1][j][k]}
                    for k in range(num_teams)
                ]
            
            team_height = 25
            center_height = team_height * num_teams
            top_padding = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "top_padding": top_padding,
                "scores":[0,0]
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


def single_elimination_tournament(request, tournament_id):
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
        if curr_match.starting_teams.exists():
            competitors += [(("[" + team.name + "]") if team in curr_match.advancers.all() else team.name) for team in curr_match.starting_teams.all()]
        if curr_match.prev_matches.exists():
            for prev_match in curr_match.prev_matches.all():
                if prev_match.advancers.exists():
                    competitors += [(("[" + team.name + "]") if team in curr_match.advancers.all() else team.name) for team in prev_match.advancers.all()]
                else:
                    competitors += ["TBD"]

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
            # this fixes one of preliminary matches, but also creates a weird empty round which gets adressed later
            if len(bracket_array) <= curr_round+1:
                bracket_array.append({})
            bracket_array[curr_round+1][base_index] = None

    #mutates bracket_array
    read_tree_from_node(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True)[0], 0, 0)

    #this gets weird of the weird empty round caused by the previous section
    bracket_array.pop()

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
    connectorWidth = 50
    bracketWidth = (matchWidth+connectorWidth)*numRounds
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
                    {"team_name": bracket_array[numRounds-i-1][j][k]}
                    for k in range(num_teams)
                ]
            
            team_height = 25
            center_height = team_height * num_teams
            top_padding = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "top_padding": top_padding,
                "scores":[0,0]
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


def single_elim_tournament(request, tournament_id):
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    context = {"tournament": tournament, "user": request.user}
    return render(request, "competitions/single_elim_tournament.html", context)


def tournaments(request):
    context = {"user": request.user}
    return render(request, "competitions/tournaments.html", context)


def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "user": request.user}
    return render(request, "competitions/competitions.html", context)


def competition(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    if competition.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    context = {"competition": competition, "user": request.user, "Status": Status}
    return render(request, "competitions/competition.html", context)


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
def judge_match(request, pk: int):
    instance = get_object_or_404(Match, pk=pk)
    user = request.user

    tournament = instance.tournament
    assert isinstance(tournament, AbstractTournament)
    competetion = tournament.competition
    assert isinstance(competetion, Competition)
    
    if not competetion.is_judgable:
        messages.error(request, "This competition is not currently open for judging.")
        raise PermissionDenied("This competition is not currently open for judging.")
    if not tournament.is_judgable:
        messages.error(request, "This tournament is not currently open for judging.")
        raise PermissionDenied("This tournament is not currently open for judging.")
    # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
    if  not (user in tournament.judges.all() \
    or user in competetion.plenary_judges.all()):# \
    #or user.is_superuser:
        messages.error(request, "You are not authorized to judge this match.")
        raise PermissionDenied("You are not authorized to judge this match.")
        #return HttpResponseRedirect(reverse('competitions:competition', args=[competetion.id]))
    winner_choices = []
    if instance.prev_matches.exists():
        winner_choice_ids = []
        for match in instance.prev_matches.all():
            winner_choice_ids.extend([x.id for x in match.advancers.all()])
        winner_choices = Team.objects.filter(id__in=winner_choice_ids)
    elif instance.starting_teams.exists():
        winner_choices = instance.starting_teams.all()
    
    if request.method == 'POST':
        form = JudgeForm(request.POST, instance=instance, possible_advancers=winner_choices)
        if form.is_valid():
            form.save()
            messages.success(request, "Match judged successfully.")
        else:
            messages.error(request, "Invalid form submission.")
            #raise PermissionDenied("Invalid form submission.")
            # ^ uncoment this line when running the test, for invalid form submission this will raise an error

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


# Prepare a map of common locations to timezone choices you wish to offer.
common_timezones = {
    "London": "Europe/London",
    "Paris": "Europe/Paris",
    "New York": "America/New_York",
}

def set_timezone(request):
    if request.method == "POST":
        request.session["django_timezone"] = request.POST["timezone"]
        return redirect("/")
    else:
        return render(request, "set-local-timezone.html", {"timezones": common_timezones})

def home(request):
    return render(request, "competitions/home.html")


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


def tournament(request, tournament_id):
    context = {"user": request.user}
    return render(request, "competitions/tournament.html", context)


def tournaments(request):
    context = {"user": request.user}
    return render(request, "competitions/tournaments.html", context)

def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "redirect_to": request.path, "user": request.user}
    return render(request, "competitions/competitions.html", context)

def competition(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    if competition.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    context = {"competition": competition, "redirect_to": request.path, "user": request.user, "Status": Status}
    return render(request, "competitions/competition.html", context)

def team(request, team_id):
    today = timezone.now().date()
    upcoming_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id), tournament__competition__start_date__lte=today, tournament__competition__end_date__gte=today, advancers=None).order_by("time")
    context = {
        'team': Team.objects.get(pk=team_id),
        'wins_list': [],
        'draws_list': [],
        'losses_list': [],
        'upcoming_matches': upcoming_matches,
    }
    return render(request, "competitions/team.html", context)

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
