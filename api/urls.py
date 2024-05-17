from django.urls import path

from .views import *

urlpatterns = [
    path('teams/', teams, name="api_teams"),
    path('tournament_form/<int:competition_id>/', tournament_form, name='api_tournamentform')
]
