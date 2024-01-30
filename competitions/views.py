from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.views.generic.edit import UpdateView
from .models import Organization, Team, Competition, Event, Ranking, SingleEliminationTournament, Match, Status
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def competitions(request):
    competition_list = Competition.objects.all()
    context = {"competition_list": competition_list, "Status": Status}
    return render(request, "competitions/competition_hub.html", context)

def not_implemented(request, *args, **kwargs):
    messages.error(request, "This feature is not yet implemented.")
    return render(request, 'skeleton.html')