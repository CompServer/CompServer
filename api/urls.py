from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .views import *

app_name = "api"
urlpatterns = [
    path('arenas/new/', new_arena, name="new_arena"),
    path('competition/<int:competition_id>/judge/<int:judge_id>/remove/', remove_judge, name="remove_judge"),
    path('teams/', teams, name="teams"),
    path('teams/new/', new_team, name="new_team"),
    path('tournament_form/<int:competition_id>/', tournament_form, name='tournamentform')
]
