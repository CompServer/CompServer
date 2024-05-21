from http.client import HTTPResponse
import re
from django.http import HttpRequest, HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from django.template import RequestContext
from competitions.models import *
from competitions.forms import RRTournamentForm, SETournamentForm
from crispy_forms.utils import render_crispy_form
import html
from competitions.views import competition

# Create your views here.

def teams(request: HttpRequest):
    sport = request.GET.get('sport')
    response = ''

    sport = get_object_or_404(Sport, pk=sport)

    for team in Team.objects.filter(sport=sport):
        response += f'<option value="{team.id}">{team.name}</option>\n'
    
    return HttpResponse(content=response)

def new_team(request: HttpRequest):
    sport_id = request.POST.get('sport')
    if sport_id:
        sport = Sport.objects.get(id=sport_id)
    else:
        sport = None
    competition_id = request.POST.get('competition')
    if competition_id:
        competition = Competition.objects.get(id=competition_id)
    else:
        competition = None

    name = html.escape(request.POST.get('new_team'))
    name = name.strip()

    response = ''
    if sport:
        if name != "":
            team = Team(name=name, sport=sport)
            team.save()
            if competition:
                competition.teams.add(team)
                return render(request, "competitions/competition.html#competition-teams", {"competition": competition})
        for team in Team.objects.filter(sport=sport):
            response += f'<option value="{team.id}">{team.name}</option>\n'
    
    return HttpResponse(content=response)


def new_arena(request: HttpRequest):
    competition_id = request.POST.get('competition')
    if competition_id:
        competition = Competition.objects.get(id=competition_id)
    else:
        competition = None

    name = html.escape(request.POST.get('new_arena'))
    name = name.strip()

    response = ''
    if competition:
        if name != "":
            arena = Arena(name=name)
            arena.save()
            competition.arenas.add(arena)
    return render(request, "competitions/competition.html#competition-arenas", {"competition": competition})


def tournament_form(request: HttpRequest, competition_id: int):
    if request.method == 'GET':
        tournament_type = str(request.GET.get('tournament_type','')).lower().strip()
    elif request.method == 'POST':
        tournament_type = str(request.POST.get('tournament_type')).lower().strip()
    else:
        raise ValueError("Invalid request method")

    competition = get_object_or_404(Competition, pk=competition_id)

    FORM_CLASS = None

    if tournament_type == 'rr':
        FORM_CLASS = RRTournamentForm
    
    elif tournament_type == 'se':
        FORM_CLASS = SETournamentForm
    else:
        raise ValueError("Invalid tournament type")

    form = FORM_CLASS(competition=competition)

    return render(request, 'CSRF_FORM.html', {'form': form, 'action': f"?competition_id={competition_id}&tournament_type={tournament_type}"})


def remove_judge(request: HttpRequest, competition_id, judge_id):
    competition = Competition.objects.get(id=competition_id)
    judge = User.objects.get(id=judge_id)
    if competition and judge:
        competition.plenary_judges.remove(judge)
    return render(request, "competitions/competition.html#competition-plenary_judges", {"competition": competition})


