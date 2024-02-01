from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path("", views.BracketView, name="bracket"),
    path("competitions", views.competitions, name="competitions"),
    path("competitions/<int:pk>", views.competition, name="competition-page"),
    path("team/<int:team_id>/", views.team_page, name="team-page"),
    path("tournaments/", views.tournaments, name="tournaments"),
    path("tournaments/<int:pk>", views.tournament, name="tournament-page"),
    # path("coach/<int:coach_id>/", views.coach_page, name="coach-page"),
]
