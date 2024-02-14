from datetime import datetime
import math

from django.contrib import messages
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

def team(request, team_id: int):
    context = {
        'team': get_object_or_404(Team, id=team_id)
    }
    return render(request, "competitions/team.html", context)

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