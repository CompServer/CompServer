from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
import math
from .models import *
from django.urls import reverse
from django.contrib.auth.models import User

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
    return render(request, "competitions/tournament.html")


def tournaments(request):
    return render(request, "competitions/tournaments.html")

def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "Status": Status, "redirect_to": request.path, "is_staff": False}
    if request.user.is_staff:
        context = {"competition_list": competition_list, "Status": Status, "redirect_to": request.path, "is_staff": True}
    return render(request, "competitions/competitions.html", context)

def competition(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)
    if competition.status == Status.ARCHIVED:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    context = {"competition": competition, "redirect_to": request.path, "is_staff": False}
    if request.user.is_staff:
        context = {"competition": competition, "redirect_to": request.path, "is_staff": True}
    return render(request, "competitions/competition.html", context)

def team(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    context = {'team': team, "is_staff": False}
    return render(request, "competitions/team.html", context)


def not_implemented(request, *args, **kwargs):
    messages.error(request, "This feature is not yet implemented.")
    return render(request, 'skeleton.html')
