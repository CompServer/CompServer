from django.urls import path

from .views import *

urlpatterns = [
    path('teams/', teams, name="api_teams"),
    path('teams/new/', new_team, name="api_new_team"),
    path('tournament_form/<int:competition_id>/', tournament_form, name='api_tournamentform')
]
