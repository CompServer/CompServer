from django.urls import path
from . import views

app_name = "competitions"
urlpatterns = [
    path("", views.BracketView, name="bracket"),
    path("competition", views.competitions, name="competitions"),
    path("competition/<int:pk>", views.not_implemented, name="competition"),
    path("team/<int:team_id>/", views.team_page, name="team"),
    path("tournament/", views.tournaments, name="tournaments"),
    path("tournament/<int:pk>", views.tournament, name="tournament"),
    # path("coach/<int:coach_id>/", views.coach_page, name="coach-page"),
]
