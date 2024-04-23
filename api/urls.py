from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .views import *

urlpatterns = [
    path('teams/', teams, name="api_teams"),
    path('tournament_form/<int:competition_id>/', tournament_form, name='api_tournamentform')
]
